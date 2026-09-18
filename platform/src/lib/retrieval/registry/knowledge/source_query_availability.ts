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
