import type { SourceQueryAvailabilityRequirement } from './types'
import { stableFingerprint } from './stable'

export type SourceQueryParameterBinding = 'global' | 'chart_and_active_build'
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

function contractFingerprint(contract: SourceQueryAvailabilityContract): string {
  return stableFingerprint(contract)
}

/*
 * Reviews are intentionally source-by-source. Do not infer membership from a
 * descriptor family or table name: a review is admitted only after the handler
 * relation, scope/build binding, and honest-empty behavior have all been read.
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
]

const CONTRACT_BY_ID = new Map(CONTRACTS.map((contract) => [contract.contract_id, contract]))
const CONTRACT_BY_DESCRIPTOR = new Map(CONTRACTS.map((contract) => [contract.descriptor_name, contract]))

export function getSourceQueryAvailabilityContract(
  contractId: string,
): SourceQueryAvailabilityContract | undefined {
  return CONTRACT_BY_ID.get(contractId)
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
      contract_sha256: contractFingerprint(contract),
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
    && requirement.contract_sha256 === contractFingerprint(contract)
    && requirement.capability_uri === contract.capability_uri
    && requirement.scope === contract.scope
    && requirement.source_ref === contract.source_refs.join(' | ')
    && ((contract.scope === 'global' && contract.parameter_binding === 'global')
      || (contract.scope === 'chart' && contract.parameter_binding === 'chart_and_active_build')))
}

export function getSourceQueryAvailabilityReviews(): readonly DescriptorSourceQueryAvailabilityReview[] {
  return CONTRACTS.map((contract) => getDescriptorSourceQueryAvailabilityReview(contract.descriptor_name)!)
}
