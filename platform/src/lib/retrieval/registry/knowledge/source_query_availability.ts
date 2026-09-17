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
const CONTRACTS: readonly SourceQueryAvailabilityContract[] = [{
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
}]

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
