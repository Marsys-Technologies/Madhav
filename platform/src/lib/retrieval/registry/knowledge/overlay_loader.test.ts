import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { CapabilityKnowledgeSnapshot } from './types'
import generatedCapabilityKnowledge from '../../../../generated/capability_knowledge.snapshot.json'

const mocks = vi.hoisted(() => ({ query: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: mocks.query }))

import {
  loadChartCapabilityOverlay,
  probeSourceQueryAvailabilityContract,
} from './overlay_loader'
import { getPinnedCapabilityKnowledgeSnapshot } from './snapshot'
import { getSourceQueryAvailabilityContract } from './source_query_availability'

const claimHash = 'a'.repeat(64)
const snapshot = {
  schema_version: '2.3.0', compatibility_version: 'planner-scu-v2', generated_at: '2026-09-13T00:00:00.000Z',
  content_hash: 'sha256:content', source_catalog_fingerprint: 'sha256:catalog', semantic_review_fingerprint: 'sha256:review', producer_contract_fingerprint: 'sha256:producer', edges: [], concept_universe: [],
  producer_semantic_bindings: [],
  census: { runtime_descriptors: 1, addressable_descriptors: 1, excluded_descriptors: 0, semantic_capabilities: 1, editorial_scus: 1, derived_scus: 0, executable_bindings: 1, unavailable_bindings: 0, publicly_named_bindings: 0, reviewed_pagination_bindings: 0, reviewed_pagination_dispositions: 1, reviewed_paginated_descriptors: 0, exhaustible_reviewed_descriptors: 0, non_exhaustible_descriptors: 0, reviewed_route_descriptors: 1, reviewed_public_descriptors: 0, reviewed_nonpublic_descriptors: 1, producer_output_claims: 1, reviewed_output_claims: 1, typed_concepts: 0, unbound_concepts: 0, isolated_scus: 1, graph_components: 1, dispositioned_isolated_scus: 1, unresolved_isolated_scus: 0, producer_semantic_bindings: 0, directly_served_producer_outputs: 0, support_only_producer_bindings: 0, unbound_active_producers: 0, undispositioned_producer_scus: 0, undispositioned_gaps: 0, exclusions: [] },
  scus: [{
    scu_id: 'scu.test', version: 1, label: 'Test', description: 'Test', kind: 'datum', domains: ['all'], concepts: [], intents: [], horizons: ['natal'], scope: 'chart', inputs: [], outputs: [],
    primary_binding_uri: 'marsys://tool/L1/test', provenance_requirements: [], freshness_policy: 'fresh', entitlement: 'native', safety_notes: [], known_gaps: [], editorial: true,
    producer_output_claims: [{ asset_id: 'ga_test', component: 'rows', output_digest_spec_sha256: claimHash, disposition: 'reviewed_output', evidence: 'fixture' }],
    bindings: [{ binding_id: 'registry:marsys://tool/L1/test', kind: 'registry_capability', relation: 'primary', capability_uri: 'marsys://tool/L1/test', input_contract: {}, output_contract: {}, pagination: 'none', executable: true }],
    source_descriptor_uris: ['marsys://tool/L1/test'],
    editorial_method: 'authored_declaration', editorial_sources: [{ source_ref: 'fixture', source_fields: ['description'] }], concept_bindings: [], gap_dispositions: [], graph_disposition: { status: 'isolated_dispositioned', rationale: 'fixture', source_refs: ['fixture'] }, producer_semantic_disposition: { status: 'not_applicable', asset_ids: [], rationale: 'No producer applies to this isolated fixture.', source_refs: ['fixture'] },
  }],
} as CapabilityKnowledgeSnapshot

const bindingContractSnapshot = () => ({
  ...snapshot,
  scus: [{
    ...snapshot.scus[0]!,
    producer_output_claims: [
      { asset_id: 'ga_primary', component: 'primary rows', output_digest_spec_sha256: claimHash, disposition: 'reviewed_output', evidence: 'fixture:primary' },
      { asset_id: 'ga_alternate', component: 'alternate rows', output_digest_spec_sha256: claimHash, disposition: 'reviewed_output', evidence: 'fixture:alternate' },
    ],
    bindings: [
      snapshot.scus[0]!.bindings[0]!,
      {
        binding_id: 'registry:marsys://tool/L1/alternate', kind: 'registry_capability', relation: 'provides',
        capability_uri: 'marsys://tool/L1/alternate', input_contract: {}, output_contract: {}, pagination: 'none', executable: true,
      },
    ],
    availability_contracts: [
      {
        binding_id: 'registry:marsys://tool/L1/test',
        requirements: [{ kind: 'producer_output', asset_id: 'ga_primary', spec_sha256: claimHash, scope: 'chart_build', source_ref: 'fixture:primary' }],
      },
      {
        binding_id: 'registry:marsys://tool/L1/alternate',
        requirements: [{ kind: 'producer_output', asset_id: 'ga_alternate', spec_sha256: claimHash, scope: 'chart_build', source_ref: 'fixture:alternate' }],
      },
    ],
  }],
} as CapabilityKnowledgeSnapshot)

const mixedValidUnknownBindingContractSnapshot = () => {
  const base = bindingContractSnapshot()
  return {
    ...base,
    scus: [{
      ...base.scus[0]!,
      availability_contracts: [...base.scus[0]!.availability_contracts!, {
        binding_id: 'registry:marsys://tool/L1/missing',
        requirements: [{ kind: 'producer_output', asset_id: 'ga_primary', spec_sha256: claimHash, scope: 'chart_build', source_ref: 'fixture:missing' }],
      }],
    }],
  } as CapabilityKnowledgeSnapshot
}

const mixedValidUnreviewedClaimContractSnapshot = () => {
  const base = bindingContractSnapshot()
  return {
    ...base,
    scus: [{
      ...base.scus[0]!,
      availability_contracts: [
        base.scus[0]!.availability_contracts![0]!,
        {
          binding_id: 'registry:marsys://tool/L1/alternate',
          requirements: [{ kind: 'producer_output', asset_id: 'ga_unreviewed', spec_sha256: claimHash, scope: 'chart_build', source_ref: 'fixture:unreviewed' }],
        },
      ],
    }],
  } as CapabilityKnowledgeSnapshot
}

const mixedValidInvalidDerivedContractSnapshot = () => {
  const base = bindingContractSnapshot()
  return {
    ...base,
    scus: [{
      ...base.scus[0]!,
      availability_contracts: [
        base.scus[0]!.availability_contracts![0]!,
        {
          binding_id: 'registry:marsys://tool/L1/alternate',
          requirements: [{
            kind: 'derived',
            scope: 'chart',
            required_binding_ids: ['registry:marsys://tool/L1/missing-derived-leg'],
            source_ref: 'fixture:missing-derived-leg',
          }],
        },
      ],
    }],
  } as CapabilityKnowledgeSnapshot
}

const sameScuDerivedLegSnapshot = () => {
  const base = bindingContractSnapshot()
  return {
    ...base,
    scus: [{
      ...base.scus[0]!,
      availability_contracts: [
        base.scus[0]!.availability_contracts![0]!,
        {
          binding_id: 'registry:marsys://tool/L1/alternate',
          requirements: [{
            kind: 'derived',
            scope: 'chart',
            required_binding_ids: ['registry:marsys://tool/L1/test'],
            source_ref: 'fixture:same-scu-derived-leg',
          }],
        },
      ],
    }],
  } as CapabilityKnowledgeSnapshot
}

const sameScuDerivedCycleSnapshot = () => {
  const base = bindingContractSnapshot()
  return {
    ...base,
    scus: [{
      ...base.scus[0]!,
      availability_contracts: [
        {
          binding_id: 'registry:marsys://tool/L1/test',
          requirements: [{
            kind: 'derived',
            scope: 'chart',
            required_binding_ids: ['registry:marsys://tool/L1/alternate'],
            source_ref: 'fixture:same-scu-cycle-primary',
          }],
        },
        {
          binding_id: 'registry:marsys://tool/L1/alternate',
          requirements: [{
            kind: 'derived',
            scope: 'chart',
            required_binding_ids: ['registry:marsys://tool/L1/test'],
            source_ref: 'fixture:same-scu-cycle-alternate',
          }],
        },
      ],
    }],
  } as CapabilityKnowledgeSnapshot
}

const primaryOnlyContractSnapshot = () => ({
  ...bindingContractSnapshot(),
  scus: [{
    ...bindingContractSnapshot().scus[0]!,
    availability_contracts: [bindingContractSnapshot().scus[0]!.availability_contracts![0]!],
  }],
} as CapabilityKnowledgeSnapshot)

const legacyAlternateSnapshot = () => ({
  ...snapshot,
  scus: [{
    ...snapshot.scus[0]!,
    bindings: [
      snapshot.scus[0]!.bindings[0]!,
      {
        binding_id: 'registry:marsys://tool/L1/legacy_alternate', kind: 'registry_capability', relation: 'provides',
        capability_uri: 'marsys://tool/L1/legacy_alternate', input_contract: {}, output_contract: {}, pagination: 'none', executable: true,
      },
    ],
  }],
} as CapabilityKnowledgeSnapshot)

const duplicateBindingContractSnapshot = () => ({
  ...snapshot,
  scus: [{
    ...snapshot.scus[0]!,
    availability_contracts: [
      {
        binding_id: 'registry:marsys://tool/L1/test',
        requirements: [{ kind: 'producer_output', asset_id: 'ga_primary', spec_sha256: claimHash, scope: 'chart_build', source_ref: 'fixture:primary' }],
      },
      {
        binding_id: 'registry:marsys://tool/L1/test',
        requirements: [{ kind: 'producer_output', asset_id: 'ga_alternate', spec_sha256: claimHash, scope: 'chart_build', source_ref: 'fixture:alternate' }],
      },
    ],
  }],
} as CapabilityKnowledgeSnapshot)

const duplicateExecutableBindingSnapshot = () => ({
  ...snapshot,
  scus: [{
    ...snapshot.scus[0]!,
    bindings: [snapshot.scus[0]!.bindings[0]!, { ...snapshot.scus[0]!.bindings[0]! }],
  }],
} as CapabilityKnowledgeSnapshot)

const crossScuDuplicateExecutableBindingSnapshot = () => ({
  ...snapshot,
  scus: [
    snapshot.scus[0]!,
    { ...snapshot.scus[0]!, scu_id: 'scu.test.duplicate' },
  ],
} as CapabilityKnowledgeSnapshot)

const malformedRuntimeContractSnapshot = () => ({
  ...snapshot,
  scus: [{
    ...snapshot.scus[0]!,
    availability_contracts: [null, {
      binding_id: 'registry:marsys://tool/L1/test',
      requirements: [null, {
        kind: 'derived',
        scope: 'chart',
        required_binding_ids: ['registry:marsys://tool/L1/test', 'registry:marsys://tool/L1/test'],
        source_ref: '',
      }],
    }],
  }],
} as CapabilityKnowledgeSnapshot)

const malformedRuntimeRequirementSnapshot = () => ({
  ...snapshot,
  scus: [{
    ...snapshot.scus[0]!,
    availability_contracts: [{
      binding_id: 'registry:marsys://tool/L1/test',
      requirements: [null, {
        kind: 'derived',
        scope: 'chart',
        required_binding_ids: ['registry:marsys://tool/L1/test', 'registry:marsys://tool/L1/test'],
        source_ref: '',
      }],
    }],
  }],
} as CapabilityKnowledgeSnapshot)

const serviceProbeContractSnapshot = () => ({
  ...snapshot,
  scus: [{
    ...snapshot.scus[0]!,
    producer_output_claims: [],
    availability_contracts: [{
      binding_id: 'registry:marsys://tool/L1/test',
      requirements: [{
        kind: 'service_probe' as const,
        asset_id: 'bg_ephemeris_engine',
        probe_id: 'ephemeris_engine',
        endpoint_identity: 'nirmana-elevation:health-probe:bg_ephemeris_engine',
        probe_contract_sha256: claimHash,
        max_age_seconds: 900,
        source_ref: 'fixture:authenticated-probe',
      }],
    }],
  }],
} as CapabilityKnowledgeSnapshot)

const COMPOSITE_BINDING_ID = 'registry:marsys://tool/L-DOMAIN/assess_composite'
const COMPOSITE_LEGS = [
  ['registry:marsys://tool/L2/query_domain_reading', 'bo_domain_reading'],
  ['registry:marsys://tool/L3/query_temporal_activation', 'ka_temporal_activation'],
  ['registry:marsys://tool/L2/query_contradictions', 'bo_contradictions'],
] as const

/** A reduced runAssessDomain-style composite: every handler leg is its own binding. */
const derivedCompositeSnapshot = () => {
  const legs = COMPOSITE_LEGS.map(([bindingId, assetId], index) => ({
    ...snapshot.scus[0]!,
    scu_id: `scu.composite.leg.${index + 1}`,
    label: `Composite leg ${index + 1}`,
    primary_binding_uri: bindingId.replace(/^registry:/, ''),
    producer_output_claims: [{
      asset_id: assetId,
      component: `${assetId} rows`,
      output_digest_spec_sha256: claimHash,
      disposition: 'reviewed_output' as const,
      evidence: `fixture:${assetId}`,
    }],
    bindings: [{
      ...snapshot.scus[0]!.bindings[0]!,
      binding_id: bindingId,
      capability_uri: bindingId.replace(/^registry:/, ''),
    }],
    availability_contracts: [{
      binding_id: bindingId,
      requirements: [{
        kind: 'producer_output' as const,
        asset_id: assetId,
        spec_sha256: claimHash,
        scope: 'chart_build' as const,
        source_ref: `fixture:${assetId}`,
      }],
    }],
  }))
  const parent = {
    ...snapshot.scus[0]!,
    scu_id: 'scu.composite.assessment',
    label: 'Composite assessment',
    primary_binding_uri: COMPOSITE_BINDING_ID.replace(/^registry:/, ''),
    producer_output_claims: [],
    bindings: [
      {
        ...snapshot.scus[0]!.bindings[0]!,
        binding_id: COMPOSITE_BINDING_ID,
        capability_uri: COMPOSITE_BINDING_ID.replace(/^registry:/, ''),
      },
      {
        binding_id: 'registry:marsys://tool/L-DOMAIN/assess_composite_alternate',
        kind: 'registry_capability' as const,
        relation: 'provides' as const,
        capability_uri: 'marsys://tool/L-DOMAIN/assess_composite_alternate',
        input_contract: {}, output_contract: {}, pagination: 'none' as const, executable: true,
      },
    ],
    availability_contracts: [{
      binding_id: COMPOSITE_BINDING_ID,
      requirements: [{
        kind: 'derived' as const,
        scope: 'chart' as const,
        required_binding_ids: COMPOSITE_LEGS.map(([bindingId]) => bindingId),
        source_ref: 'fixture:runAssessDomain:mandatory-handler-legs',
      }],
    }],
  }
  return { ...snapshot, scus: [parent, ...legs] } as CapabilityKnowledgeSnapshot
}

const derivedCompositeWithInvalidChildSnapshot = () => {
  const base = derivedCompositeSnapshot()
  const [parent, invalidChild, ...remainingLegs] = base.scus
  return {
    ...base,
    scus: [
      parent!,
      {
        ...invalidChild!,
        producer_output_claims: invalidChild!.producer_output_claims!.map((claim) => ({
          ...claim,
          output_digest_spec_sha256: 'b'.repeat(64),
        })),
      },
      ...remainingLegs,
    ],
  } as CapabilityKnowledgeSnapshot
}

const compositeWithInvalidChildSiblingSnapshot = () => {
  const parentBindingId = 'registry:marsys://tool/L-DOMAIN/assess_parent'
  const childBindingId = 'registry:marsys://tool/L2/query_child'
  const childSiblingBindingId = 'registry:marsys://tool/L2/query_child_sibling'
  const parent = {
    ...snapshot.scus[0]!,
    scu_id: 'scu.parent.composite',
    primary_binding_uri: parentBindingId.replace(/^registry:/, ''),
    producer_output_claims: [],
    bindings: [{ ...snapshot.scus[0]!.bindings[0]!, binding_id: parentBindingId, capability_uri: parentBindingId.replace(/^registry:/, '') }],
    availability_contracts: [{
      binding_id: parentBindingId,
      requirements: [{ kind: 'derived' as const, scope: 'chart' as const, required_binding_ids: [childBindingId], source_ref: 'fixture:parent-child' }],
    }],
  }
  const child = {
    ...snapshot.scus[0]!,
    scu_id: 'scu.child.with-invalid-sibling',
    primary_binding_uri: childBindingId.replace(/^registry:/, ''),
    producer_output_claims: [{ asset_id: 'ga_child', component: 'child rows', output_digest_spec_sha256: claimHash, disposition: 'reviewed_output' as const, evidence: 'fixture:child' }],
    bindings: [
      { ...snapshot.scus[0]!.bindings[0]!, binding_id: childBindingId, capability_uri: childBindingId.replace(/^registry:/, '') },
      { binding_id: childSiblingBindingId, kind: 'registry_capability' as const, relation: 'provides' as const, capability_uri: childSiblingBindingId.replace(/^registry:/, ''), input_contract: {}, output_contract: {}, pagination: 'none' as const, executable: true },
    ],
    availability_contracts: [
      { binding_id: childBindingId, requirements: [{ kind: 'producer_output' as const, asset_id: 'ga_child', spec_sha256: claimHash, scope: 'chart_build' as const, source_ref: 'fixture:child' }] },
      { binding_id: childSiblingBindingId, requirements: [{ kind: 'producer_output' as const, asset_id: 'ga_unreviewed', spec_sha256: claimHash, scope: 'chart_build' as const, source_ref: 'fixture:child-sibling' }] },
    ],
  }
  return { ...snapshot, scus: [parent, child] } as CapabilityKnowledgeSnapshot
}

function receipt(asset_id: string, overrides: Partial<Record<string, unknown>> = {}) {
  return {
    active_build_id: 'build-1', active_build_status: 'completed',
    asset_id, chart_id: 'chart-1', build_id: 'build-1', receipt_version: 'v1', receipt_state: 'proven',
    output_digest_spec_sha256: claimHash, observed_at: '2026-09-13T00:00:00Z', freshness_state: 'fresh', unknown_reasons: [], freshness_reasons: [],
    ...overrides,
  }
}

function validServiceProbePayload() {
  return {
    registry_fingerprint_sha256: 'c'.repeat(64),
    analysis_digest: 'd'.repeat(64),
    probe_contract_sha256: claimHash,
    response_digest: 'e'.repeat(64),
    detector_observation: {
      probe_type: 'ephemeris_engine',
      runner_revision: 'candidate-sha',
      request_started_at: '2026-09-16T23:59:59.000Z',
      request_ended_at: '2026-09-17T00:00:01.000Z',
      result: { status: 'GREEN', checks: [{ check: 'forensic-anchor', passed: true }] },
    },
  }
}

function serviceProbeEvidence(overrides: Partial<Record<string, unknown>> = {}) {
  return {
    asset_id: 'bg_ephemeris_engine',
    source_kind: 'server_reconstructed',
    source_ref: 'nirmana-elevation:health-probe:bg_ephemeris_engine',
    observed_at: '2026-09-17T00:00:00.000Z',
    evidence_payload: validServiceProbePayload(),
    ...overrides,
  }
}

function serviceProbeAnchor(service_probe_evidence: unknown) {
  return {
    active_build_id: 'build-1', active_build_status: 'completed',
    asset_id: null, chart_id: null, build_id: null, receipt_version: null, receipt_state: null,
    output_digest_spec_sha256: null, observed_at: null, freshness_state: null, unknown_reasons: [], freshness_reasons: [],
    service_probe_evidence,
  }
}

function failedServiceProbeEvidence() {
  const payload = validServiceProbePayload()
  return serviceProbeEvidence({
    evidence_payload: {
      ...payload,
      detector_observation: {
        ...payload.detector_observation,
        result: { status: 'degraded', checks: [{ check: 'forensic-anchor', passed: false }] },
      },
    },
  })
}

function staleServiceProbeEvidence() {
  const payload = validServiceProbePayload()
  return serviceProbeEvidence({
    observed_at: '2026-09-16T23:40:00.000Z',
    evidence_payload: {
      ...payload,
      detector_observation: {
        ...payload.detector_observation,
        request_started_at: '2026-09-16T23:39:59.000Z',
        request_ended_at: '2026-09-16T23:40:01.000Z',
      },
    },
  })
}

beforeEach(() => {
  vi.clearAllMocks()
})

describe('source-query parameter binding', () => {
  const contextContract = {
    contract_id: 'source-query:test-chart-context:v1',
    descriptor_name: 'test_chart_context',
    capability_uri: 'marsys://tool/L4/test_chart_context',
    scope: 'chart' as const,
    parameter_binding: 'chart_with_active_build_context' as const,
    empty_semantics: 'query_success_is_available' as const,
    sql: 'SELECT source_id FROM source_table WHERE chart_id = $1::uuid LIMIT 0',
    source_refs: ['fixture:chart-context'],
  }

  it('keeps a chart-context source query dark when no active completed build exists', async () => {
    const query = vi.fn()

    const gaps = await probeSourceQueryAvailabilityContract(contextContract, 'chart-1', null, query)

    expect(gaps).toEqual([
      'source-query:test-chart-context:v1 requires an active completed build context for the selected chart.',
    ])
    expect(query).not.toHaveBeenCalled()
  })

  it('executes a chart-context source query with chart_id only', async () => {
    const query = vi.fn().mockResolvedValue({ rows: [] })

    const gaps = await probeSourceQueryAvailabilityContract(contextContract, 'chart-1', 'build-1', query)

    expect(gaps).toEqual([])
    expect(query).toHaveBeenCalledExactlyOnceWith(contextContract.sql, ['chart-1'])
  })

  it('fails temporal availability closed when its source or active build is unavailable', async () => {
    const temporalContract = getSourceQueryAvailabilityContract('source-query:query-temporal-activation:v1')!
    const query = vi.fn()

    await expect(probeSourceQueryAvailabilityContract(temporalContract, 'chart-1', null, query)).resolves.toEqual([
      'source-query:query-temporal-activation:v1 requires an active completed build context for the selected chart.',
    ])
    expect(query).not.toHaveBeenCalled()

    query.mockRejectedValueOnce(new Error('permission denied'))
    await expect(probeSourceQueryAvailabilityContract(temporalContract, 'chart-1', 'build-1', query)).resolves.toEqual([
      'source-query:query-temporal-activation:v1 could not execute its authenticated source query.',
    ])
  })

  it('preserves row-bound chart-and-active-build query parameters', async () => {
    const query = vi.fn().mockResolvedValue({ rows: [] })
    const rowBoundContract = {
      ...contextContract,
      contract_id: 'source-query:test-chart-build:v1',
      parameter_binding: 'chart_and_active_build' as const,
      sql: 'SELECT source_id FROM source_table WHERE chart_id = $1::uuid AND build_id = $2::uuid LIMIT 0',
    }

    const gaps = await probeSourceQueryAvailabilityContract(rowBoundContract, 'chart-1', 'build-1', query)

    expect(gaps).toEqual([])
    expect(query).toHaveBeenCalledExactlyOnceWith(rowBoundContract.sql, ['chart-1', 'build-1'])
  })
})

describe('chart capability overlay loader', () => {
  it.each([
    ['scu.catalog.query_yoga_catalog', 'registry:marsys://tool/L0/query_yoga_catalog', 'brahma_yoga_catalog', []],
    ['scu.catalog.query_dosha_catalog', 'registry:marsys://tool/L0/query_dosha_catalog', 'brahma_dosha_catalog', []],
    ['scu.catalog.query_compendium_index', 'registry:marsys://tool/L0/query_compendium_index', 'brahma_compendium_index', []],
    ['scu.kala.temporal_activation', 'registry:marsys://tool/L3/query_temporal_activation', 'kala_activation', ['chart-1']],
  ])('treats a successful reviewed source query with zero rows as available for %s', async (scuId, bindingId, relation, expectedParams) => {
    const sourceSnapshot = generatedCapabilityKnowledge as CapabilityKnowledgeSnapshot
    const sourceScu = sourceSnapshot.scus.find((scu) => scu.scu_id === scuId)!
    mocks.query.mockImplementation(async (sql) => sql.includes('WITH latest_build AS')
      ? { rows: [serviceProbeAnchor([])] }
      : { rows: [] })

    const availability = (await loadChartCapabilityOverlay(sourceSnapshot, 'chart-1')).availability
      .find((item) => item.scu_id === sourceScu.scu_id)

    expect(availability).toMatchObject({
      state: 'available',
      freshness: 'unknown',
      available_binding_ids: [bindingId],
      asset_receipts: [],
      gaps: [],
    })
    const sourceCall = mocks.query.mock.calls.find((call) => call[0].includes(`FROM ${relation}`))
    expect(sourceCall?.[0]).toContain(`FROM ${relation}`)
    expect(sourceCall?.[1]).toEqual(expectedParams)
  })

  it.each([
    ['scu.catalog.query_yoga_catalog', 'source-query:query-yoga-catalog:v1', 'brahma_yoga_catalog'],
    ['scu.catalog.query_dosha_catalog', 'source-query:query-dosha-catalog:v1', 'brahma_dosha_catalog'],
    ['scu.catalog.query_compendium_index', 'source-query:query-compendium-index:v1', 'brahma_compendium_index'],
    ['scu.kala.temporal_activation', 'source-query:query-temporal-activation:v1', 'kala_activation'],
  ])('keeps %s dark when its authenticated source query fails', async (scuId, contractId, relation) => {
    const sourceSnapshot = generatedCapabilityKnowledge as CapabilityKnowledgeSnapshot
    const sourceScu = sourceSnapshot.scus.find((scu) => scu.scu_id === scuId)!
    mocks.query.mockImplementation(async (sql) => {
      if (sql.includes('WITH latest_build AS')) return { rows: [serviceProbeAnchor([])] }
      if (sql.includes(`FROM ${relation}`)) throw new Error('permission denied')
      return { rows: [] }
    })

    const availability = (await loadChartCapabilityOverlay(sourceSnapshot, 'chart-1')).availability
      .find((item) => item.scu_id === sourceScu.scu_id)

    expect(availability).toMatchObject({ state: 'dark', available_binding_ids: [] })
    expect(availability?.gaps).toContain(`${contractId} could not execute its authenticated source query.`)
  })

  it('enables only the reviewed dasha and gestalt primary bindings from their exact receipts', async () => {
    const sourceSnapshot = generatedCapabilityKnowledge as CapabilityKnowledgeSnapshot
    const dashas = sourceSnapshot.scus.find((scu) => scu.scu_id === 'scu.catalog.get_dashas')!
    const gestalt = sourceSnapshot.scus.find((scu) => scu.scu_id === 'scu.catalog.query_chart_gestalt')!
    const dashaReceipt = receipt('ga_dashas', { output_digest_spec_sha256: '573e8aa1a0298d6626784b5ff540c004fd4d2298b6b47d2980a447acdc193d14' })
    const gestaltReceipt = receipt('bo_chart_gestalt', { output_digest_spec_sha256: '2fae5316fbc9a445377a279716f4b1ea5834954b21a54e77f79fe3c6a2b3721e' })

    mocks.query.mockResolvedValueOnce({ rows: [dashaReceipt, gestaltReceipt] })
    let availability = (await loadChartCapabilityOverlay(sourceSnapshot, 'chart-1')).availability
    expect(availability.find((item) => item.scu_id === dashas.scu_id))
      .toMatchObject({ state: 'available', available_binding_ids: ['registry:marsys://tool/L1/get_dashas'] })
    expect(availability.find((item) => item.scu_id === gestalt.scu_id))
      .toMatchObject({ state: 'available', available_binding_ids: ['registry:marsys://tool/L2/query_chart_gestalt'] })

    mocks.query.mockResolvedValueOnce({ rows: [gestaltReceipt] })
    availability = (await loadChartCapabilityOverlay(sourceSnapshot, 'chart-1')).availability
    expect(availability.find((item) => item.scu_id === dashas.scu_id))
      .toMatchObject({ state: 'dark', available_binding_ids: [] })

    mocks.query.mockResolvedValueOnce({ rows: [dashaReceipt, receipt('bo_chart_gestalt', { output_digest_spec_sha256: 'b'.repeat(64) })] })
    availability = (await loadChartCapabilityOverlay(sourceSnapshot, 'chart-1')).availability
    expect(availability.find((item) => item.scu_id === gestalt.scu_id))
      .toMatchObject({ state: 'incompatible', available_binding_ids: [] })
  })

  it('keeps uncontracted bindings dark when the SCU has an authored contract', async () => {
    mocks.query.mockResolvedValue({ rows: [receipt('ga_primary'), receipt('ga_test')] })

    expect((await loadChartCapabilityOverlay(primaryOnlyContractSnapshot(), 'chart-1')).availability[0])
      .toMatchObject({ available_binding_ids: ['registry:marsys://tool/L1/test'] })
  })

  it('uses a legacy receipt fallback for the primary binding only', async () => {
    mocks.query.mockResolvedValue({ rows: [receipt('ga_test')] })

    expect((await loadChartCapabilityOverlay(legacyAlternateSnapshot(), 'chart-1')).availability[0])
      .toMatchObject({ available_binding_ids: ['registry:marsys://tool/L1/test'] })
  })

  it('admits generated temporal activation from its own source query while admitting alternate bindings with complete exact contracts', async () => {
    const sourceSnapshot = generatedCapabilityKnowledge as CapabilityKnowledgeSnapshot
    const temporal = sourceSnapshot.scus.find((scu) => scu.scu_id === 'scu.kala.temporal_activation')!
    const wealth = sourceSnapshot.scus.find((scu) => scu.scu_id === 'scu.finance.prosperity_assessment')!
    const yoga = sourceSnapshot.scus.find((scu) => scu.scu_id === 'scu.yoga.firing_and_cancellation')!
    const rows = [wealth, yoga].flatMap((scu) => (scu.producer_output_claims ?? [])
      .filter((claim) => claim.disposition === 'reviewed_output')
      .map((claim) => receipt(claim.asset_id, { output_digest_spec_sha256: claim.output_digest_spec_sha256 })))
    mocks.query.mockImplementation(async (sql) => sql.includes('FROM kala_activation')
      ? { rows: [] }
      : { rows })

    const availability = (await loadChartCapabilityOverlay(sourceSnapshot, 'chart-1')).availability
    expect(availability.find((item) => item.scu_id === temporal.scu_id))
      .toMatchObject({ state: 'available', available_binding_ids: ['registry:marsys://tool/L3/query_temporal_activation'] })
    expect(availability.find((item) => item.scu_id === wealth.scu_id))
      .toMatchObject({ available_binding_ids: ['registry:marsys://tool/L-DOMAIN/assess_wealth'] })
    expect(availability.find((item) => item.scu_id === yoga.scu_id))
      .toMatchObject({ available_binding_ids: ['mcp:yoga_activation_by_dasha', 'registry:marsys://tool/L1/get_yoga_firings'] })
  })

  it('fails closed when duplicate contracts name one binding with different producer assets', async () => {
    mocks.query.mockResolvedValue({ rows: [receipt('ga_primary')] })

    expect((await loadChartCapabilityOverlay(duplicateBindingContractSnapshot(), 'chart-1')).availability[0])
      .toMatchObject({ state: 'dark', available_binding_ids: [] })
  })

  it('fails the whole SCU closed when a sibling contract names an unknown binding', async () => {
    mocks.query.mockResolvedValue({ rows: [receipt('ga_primary'), receipt('ga_alternate')] })

    expect((await loadChartCapabilityOverlay(mixedValidUnknownBindingContractSnapshot(), 'chart-1')).availability[0])
      .toMatchObject({
        state: 'dark',
        available_binding_ids: [],
        gaps: ['Binding availability contract names an unknown or non-executable local binding.'],
      })
  })

  it('fails the whole SCU closed when a sibling producer requirement lacks its reviewed claim', async () => {
    mocks.query.mockResolvedValue({ rows: [receipt('ga_primary'), receipt('ga_unreviewed')] })

    expect((await loadChartCapabilityOverlay(mixedValidUnreviewedClaimContractSnapshot(), 'chart-1')).availability[0])
      .toMatchObject({
        state: 'dark',
        available_binding_ids: [],
        gaps: ['Producer-output availability requirement has no same-SCU reviewed output claim with the exact asset and SHA-256.'],
      })
  })

  it('fails the whole SCU closed when a sibling derived contract is semantically invalid', async () => {
    mocks.query.mockResolvedValue({ rows: [receipt('ga_primary'), receipt('ga_alternate')] })

    expect((await loadChartCapabilityOverlay(mixedValidInvalidDerivedContractSnapshot(), 'chart-1')).availability[0])
      .toMatchObject({
        state: 'dark',
        available_binding_ids: [],
        gaps: ['Derived availability leg registry:marsys://tool/L1/missing-derived-leg has no scope-compatible executable binding.'],
      })
  })

  it('evaluates a valid same-SCU derived leg when its exact evidence is sufficient', async () => {
    mocks.query.mockResolvedValue({ rows: [receipt('ga_primary')] })

    expect((await loadChartCapabilityOverlay(sameScuDerivedLegSnapshot(), 'chart-1')).availability[0])
      .toMatchObject({
        state: 'available',
        available_binding_ids: [
          'registry:marsys://tool/L1/alternate',
          'registry:marsys://tool/L1/test',
        ],
      })
  })

  it('darkens a same-SCU two-binding derived cycle without recursing indefinitely', async () => {
    mocks.query.mockResolvedValue({ rows: [receipt('ga_primary'), receipt('ga_alternate')] })

    expect((await loadChartCapabilityOverlay(sameScuDerivedCycleSnapshot(), 'chart-1')).availability[0])
      .toMatchObject({
        state: 'dark',
        available_binding_ids: [],
        gaps: ['Derived availability leg registry:marsys://tool/L1/alternate: Derived availability leg registry:marsys://tool/L1/test: Derived availability contracts contain a cycle.'],
      })
  })

  it('does not let a semantically invalid child contract promote a composite parent', async () => {
    mocks.query.mockResolvedValue({ rows: COMPOSITE_LEGS.map(([, assetId]) => receipt(assetId)) })

    const availability = (await loadChartCapabilityOverlay(derivedCompositeWithInvalidChildSnapshot(), 'chart-1')).availability
    expect(availability.find((item) => item.scu_id === 'scu.composite.assessment')).toMatchObject({
      state: 'dark',
      available_binding_ids: [],
      gaps: [expect.stringContaining('Producer-output availability requirement has no same-SCU reviewed output claim')],
    })
    expect(availability.find((item) => item.scu_id === 'scu.composite.leg.1')).toMatchObject({
      state: 'dark',
      available_binding_ids: [],
      gaps: ['Producer-output availability requirement has no same-SCU reviewed output claim with the exact asset and SHA-256.'],
      })
  })

  it('does not let a valid child binding promote a parent when its sibling makes the child SCU dark', async () => {
    mocks.query.mockResolvedValue({ rows: [receipt('ga_child')] })

    const availability = (await loadChartCapabilityOverlay(compositeWithInvalidChildSiblingSnapshot(), 'chart-1')).availability
    expect(availability.find((item) => item.scu_id === 'scu.parent.composite')).toMatchObject({
      state: 'dark',
      available_binding_ids: [],
      gaps: [expect.stringContaining('Producer-output availability requirement has no same-SCU reviewed output claim')],
    })
    expect(availability.find((item) => item.scu_id === 'scu.child.with-invalid-sibling')).toMatchObject({
      state: 'dark',
      available_binding_ids: [],
      gaps: ['Producer-output availability requirement has no same-SCU reviewed output claim with the exact asset and SHA-256.'],
    })
  })

  it('treats a duplicate executable binding ID as ambiguous and dark', async () => {
    mocks.query.mockResolvedValue({ rows: [receipt('ga_test')] })

    const availability = (await loadChartCapabilityOverlay(duplicateExecutableBindingSnapshot(), 'chart-1')).availability[0]!
    expect(availability).toMatchObject({ state: 'dark', available_binding_ids: [] })
    expect(availability.gaps).toContain('Duplicate executable binding ID prevents a safe availability selection.')
  })

  it('treats an executable binding ID duplicated across SCUs as ambiguous and dark', async () => {
    mocks.query.mockResolvedValue({ rows: [receipt('ga_test')] })

    const availability = (await loadChartCapabilityOverlay(crossScuDuplicateExecutableBindingSnapshot(), 'chart-1')).availability
    expect(availability).toHaveLength(2)
    expect(availability).toEqual(expect.arrayContaining([
      expect.objectContaining({ state: 'dark', available_binding_ids: [], gaps: expect.arrayContaining([
        'Duplicate executable binding ID prevents a safe availability selection.',
      ]) }),
    ]))
  })

  it('fails malformed runtime contracts and requirements closed without throwing', async () => {
    mocks.query.mockResolvedValue({ rows: [receipt('ga_test')] })

    await expect(loadChartCapabilityOverlay(malformedRuntimeContractSnapshot(), 'chart-1')).resolves.toMatchObject({
      availability: [expect.objectContaining({ state: 'dark', available_binding_ids: [] })],
    })
    await expect(loadChartCapabilityOverlay(malformedRuntimeRequirementSnapshot(), 'chart-1')).resolves.toMatchObject({
      availability: [expect.objectContaining({
        state: 'dark',
        available_binding_ids: [],
        gaps: expect.arrayContaining(['Binding availability contract contains a malformed or unsupported requirement.']),
      })],
    })
  })

  it('enables a derived composite only when every mandatory handler leg has fresh exact evidence', async () => {
    mocks.query.mockResolvedValue({ rows: COMPOSITE_LEGS.map(([, assetId]) => receipt(assetId)) })

    const availability = (await loadChartCapabilityOverlay(derivedCompositeSnapshot(), 'chart-1')).availability
    expect(availability.find((item) => item.scu_id === 'scu.composite.assessment')).toMatchObject({
      state: 'partial',
      available_binding_ids: [COMPOSITE_BINDING_ID],
    })
  })

  it.each(COMPOSITE_LEGS)('keeps a derived composite dark when mandatory leg %s is absent', async (missingBindingId, missingAssetId) => {
    mocks.query.mockResolvedValue({ rows: COMPOSITE_LEGS
      .filter(([, assetId]) => assetId !== missingAssetId)
      .map(([, assetId]) => receipt(assetId)) })

    const availability = (await loadChartCapabilityOverlay(derivedCompositeSnapshot(), 'chart-1')).availability
      .find((item) => item.scu_id === 'scu.composite.assessment')!
    expect(availability).toMatchObject({ state: 'dark', available_binding_ids: [] })
    expect(availability.gaps).toContainEqual(expect.stringContaining(missingBindingId))
  })

  it.each([
    ['stale', receipt('bo_domain_reading', { freshness_state: 'stale', freshness_reasons: ['stale'] })],
    ['mismatched', receipt('bo_domain_reading', { output_digest_spec_sha256: 'b'.repeat(64) })],
  ])('keeps a derived composite dark on %s mandatory-leg evidence', async (_state, badLegReceipt) => {
    mocks.query.mockResolvedValue({ rows: [
      badLegReceipt,
      receipt('ka_temporal_activation'),
      receipt('bo_contradictions'),
    ] })

    expect((await loadChartCapabilityOverlay(derivedCompositeSnapshot(), 'chart-1')).availability
      .find((item) => item.scu_id === 'scu.composite.assessment'))
      .toMatchObject({ available_binding_ids: [] })
  })

  it('never promotes an alternate composite binding from adjacent receipts', async () => {
    mocks.query.mockResolvedValue({ rows: [
      ...COMPOSITE_LEGS.map(([, assetId]) => receipt(assetId)),
      receipt('ga_unrelated_alternate'),
    ] })

    expect((await loadChartCapabilityOverlay(derivedCompositeSnapshot(), 'chart-1')).availability
      .find((item) => item.scu_id === 'scu.composite.assessment'))
      .toMatchObject({ available_binding_ids: [COMPOSITE_BINDING_ID] })
  })

  it('enables a binding only from a fresh, exact, authenticated service-probe receipt', async () => {
    mocks.query.mockResolvedValue({ rows: [serviceProbeAnchor([serviceProbeEvidence()])] })

    const availability = (await loadChartCapabilityOverlay(
      serviceProbeContractSnapshot(), 'chart-1', undefined, new Date('2026-09-17T00:05:00.000Z'),
    )).availability[0]

    expect(availability).toMatchObject({
      state: 'available',
      available_binding_ids: ['registry:marsys://tool/L1/test'],
    })
    expect(mocks.query.mock.calls[0]?.[0]).toContain('nirmana_elevation_campaign_events')
    expect(mocks.query.mock.calls[0]?.[0]).toContain('FROM service_probe_evidence service')
    expect(mocks.query.mock.calls[0]?.[1]).toEqual(expect.arrayContaining([[], 'chart-1', ['bg_ephemeris_engine']]))
  })

  it.each([
    ['wrong endpoint identity', serviceProbeEvidence({ source_ref: 'nirmana-elevation:health-probe:bg_other_engine' })],
    ['wrong configuration version', serviceProbeEvidence({ evidence_payload: { ...validServiceProbePayload(), probe_contract_sha256: 'b'.repeat(64) } })],
    ['failed check', failedServiceProbeEvidence()],
    ['stale observation', staleServiceProbeEvidence()],
    ['malformed evidence', serviceProbeEvidence({ evidence_payload: { probe_contract_sha256: claimHash, detector_observation: { probe_type: 'ephemeris_engine', runner_revision: '', result: { status: 'GREEN', checks: [] } } } })],
  ])('fails closed on %s service-probe evidence', async (_case, evidence) => {
    mocks.query.mockResolvedValue({ rows: [serviceProbeAnchor([evidence])] })

    expect((await loadChartCapabilityOverlay(
      serviceProbeContractSnapshot(), 'chart-1', undefined, new Date('2026-09-17T00:05:00.000Z'),
    )).availability[0]).toMatchObject({ state: 'dark', available_binding_ids: [] })
  })

  it('exposes executable bindings only from their own exact producer receipts', async () => {
    mocks.query.mockResolvedValue({ rows: [receipt('ga_primary'), receipt('ga_alternate')] })

    const availability = (await loadChartCapabilityOverlay(bindingContractSnapshot(), 'chart-1')).availability[0]

    expect(availability).toMatchObject({
      state: 'available',
      available_binding_ids: ['registry:marsys://tool/L1/alternate', 'registry:marsys://tool/L1/test'],
    })
    expect(mocks.query.mock.calls[0]?.[1]).toEqual(expect.arrayContaining([['ga_alternate', 'ga_primary']]))
  })

  it('does not let one reviewed editorial route receipt enable the wealth routes in the generated snapshot', async () => {
    const generatedSnapshot = getPinnedCapabilityKnowledgeSnapshot()
    const source = generatedSnapshot.scus.find((scu) => scu.scu_id === 'scu.bodha.mechanism.network')!
    const sourceContract = source.availability_contracts![0]!
    const sourceRequirement = sourceContract.requirements.find((requirement) => requirement.kind === 'producer_output')!
    const targetBindingIds = ['registry:marsys://tool/L-DOMAIN/assess_wealth']

    mocks.query.mockResolvedValue({ rows: [receipt(sourceRequirement.asset_id, {
      output_digest_spec_sha256: sourceRequirement.spec_sha256,
    })] })

    const availability = (await loadChartCapabilityOverlay(generatedSnapshot, 'chart-1')).availability
    expect(availability.find((item) => item.scu_id === source.scu_id)).toMatchObject({
      available_binding_ids: [sourceContract.binding_id],
    })
    for (const bindingId of targetBindingIds) {
      expect(availability.some((item) => item.available_binding_ids.includes(bindingId))).toBe(false)
    }
  })

  it.each([
    ['stale', receipt('ga_primary'), receipt('ga_alternate', { freshness_state: 'stale', freshness_reasons: ['stale'] })],
    ['mismatched', receipt('ga_primary'), receipt('ga_alternate', { output_digest_spec_sha256: 'b'.repeat(64) })],
    ['missing', receipt('ga_primary')],
  ])('does not activate a binding with %s producer evidence', async (_case, ...rows) => {
    mocks.query.mockResolvedValue({ rows })

    expect((await loadChartCapabilityOverlay(bindingContractSnapshot(), 'chart-1')).availability[0])
      .toMatchObject({ available_binding_ids: ['registry:marsys://tool/L1/test'] })
  })

  it('exposes a binding only when every selected partition is proven, fresh, and spec-matched', async () => {
    mocks.query.mockResolvedValue({ rows: [{
      active_build_id: 'build-1', active_build_status: 'completed',
      asset_id: 'ga_test', chart_id: 'chart-1', build_id: 'build-1', receipt_version: 'v1', receipt_state: 'proven',
      output_digest_spec_sha256: claimHash, observed_at: '2026-09-13T00:00:00Z', freshness_state: 'fresh', unknown_reasons: [], freshness_reasons: [],
    }] })
    const overlay = await loadChartCapabilityOverlay(snapshot, 'chart-1')
    expect(overlay.availability[0]).toMatchObject({ state: 'available', available_binding_ids: ['registry:marsys://tool/L1/test'] })
    expect(overlay.build_id).toBe('build-1')
    expect(mocks.query.mock.calls[0]?.[0]).toContain('ORDER BY ended_at DESC NULLS LAST, id DESC')
    expect(mocks.query.mock.calls[0]?.[0]).toContain('p.build_id=latest_build.build_id')
  })

  it('fails closed on a mismatched output specification or unavailable provenance', async () => {
    mocks.query.mockResolvedValueOnce({ rows: [{
      active_build_id: 'build-1', active_build_status: 'completed',
      asset_id: 'ga_test', chart_id: 'chart-1', build_id: 'build-1', receipt_version: 'v1', receipt_state: 'proven',
      output_digest_spec_sha256: 'b'.repeat(64), observed_at: '2026-09-13T00:00:00Z', freshness_state: 'fresh', unknown_reasons: [], freshness_reasons: [],
    }] })
    expect((await loadChartCapabilityOverlay(snapshot, 'chart-1')).availability[0]?.state).toBe('incompatible')

    mocks.query.mockRejectedValueOnce(new Error('offline'))
    expect((await loadChartCapabilityOverlay(snapshot, 'chart-1')).availability[0]).toMatchObject({ state: 'dark', available_binding_ids: [] })
  })

  it('ignores a proven receipt from a superseded chart build', async () => {
    mocks.query.mockResolvedValue({ rows: [{
      active_build_id: 'build-2', active_build_status: 'completed',
      asset_id: 'ga_test', chart_id: 'chart-1', build_id: 'build-1', receipt_version: 'v1', receipt_state: 'proven',
      output_digest_spec_sha256: claimHash, observed_at: '2026-09-13T00:00:00Z', freshness_state: 'fresh', unknown_reasons: [], freshness_reasons: [],
    }] })
    expect((await loadChartCapabilityOverlay(snapshot, 'chart-1')).availability[0]).toMatchObject({
      state: 'dark',
      available_binding_ids: [],
      asset_receipts: [expect.objectContaining({ state: 'missing', build_id: null })],
    })
  })

  it('uses active chart evidence instead of stale chart or global rows', async () => {
    mocks.query.mockResolvedValue({ rows: [
      {
        active_build_id: 'build-2', active_build_status: 'completed',
        asset_id: 'ga_test', chart_id: 'chart-1', build_id: 'build-1', receipt_version: 'old', receipt_state: 'proven',
        output_digest_spec_sha256: 'b'.repeat(64), observed_at: '2026-09-12T00:00:00Z', freshness_state: 'fresh', unknown_reasons: [], freshness_reasons: [],
      },
      {
        active_build_id: 'build-2', active_build_status: 'completed',
        asset_id: 'ga_test', chart_id: null, build_id: null, receipt_version: 'global', receipt_state: 'unknown',
        output_digest_spec_sha256: claimHash, observed_at: '2026-09-12T00:00:00Z', freshness_state: 'unknown', unknown_reasons: ['global-not-selected'], freshness_reasons: [],
      },
      {
        active_build_id: 'build-2', active_build_status: 'completed',
        asset_id: 'ga_test', chart_id: 'chart-1', build_id: 'build-2', receipt_version: 'current', receipt_state: 'proven',
        output_digest_spec_sha256: claimHash, observed_at: '2026-09-13T00:00:00Z', freshness_state: 'fresh', unknown_reasons: [], freshness_reasons: [],
      },
    ] })
    const availability = (await loadChartCapabilityOverlay(snapshot, 'chart-1')).availability[0]
    expect(availability).toMatchObject({
      state: 'available',
      asset_receipts: [expect.objectContaining({ state: 'passed', build_id: 'build-2' })],
    })
  })

  it('uses global evidence when no active-build chart receipt exists', async () => {
    mocks.query.mockResolvedValue({ rows: [
      {
        active_build_id: 'build-2', active_build_status: 'completed',
        asset_id: 'ga_test', chart_id: 'chart-1', build_id: 'build-1', receipt_version: 'old', receipt_state: 'proven',
        output_digest_spec_sha256: claimHash, observed_at: '2026-09-12T00:00:00Z', freshness_state: 'fresh', unknown_reasons: [], freshness_reasons: [],
      },
      {
        active_build_id: 'build-2', active_build_status: 'completed',
        asset_id: 'ga_test', chart_id: null, build_id: null, receipt_version: 'global', receipt_state: 'proven',
        output_digest_spec_sha256: claimHash, observed_at: '2026-09-13T00:00:00Z', freshness_state: 'fresh', unknown_reasons: [], freshness_reasons: [],
      },
    ] })
    expect((await loadChartCapabilityOverlay(snapshot, 'chart-1')).availability[0]).toMatchObject({
      state: 'available',
      asset_receipts: [expect.objectContaining({ state: 'passed', build_id: null })],
    })
  })
})
