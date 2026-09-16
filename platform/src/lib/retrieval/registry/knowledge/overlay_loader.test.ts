import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { CapabilityKnowledgeSnapshot } from './types'

const mocks = vi.hoisted(() => ({ query: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: mocks.query }))

import { loadChartCapabilityOverlay } from './overlay_loader'
import { getPinnedCapabilityKnowledgeSnapshot } from './snapshot'

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

function receipt(asset_id: string, overrides: Partial<Record<string, unknown>> = {}) {
  return {
    active_build_id: 'build-1', active_build_status: 'completed',
    asset_id, chart_id: 'chart-1', build_id: 'build-1', receipt_version: 'v1', receipt_state: 'proven',
    output_digest_spec_sha256: claimHash, observed_at: '2026-09-13T00:00:00Z', freshness_state: 'fresh', unknown_reasons: [], freshness_reasons: [],
    ...overrides,
  }
}

beforeEach(() => {
  vi.clearAllMocks()
})

describe('chart capability overlay loader', () => {
  it('fails closed when duplicate contracts name one binding with different producer assets', async () => {
    mocks.query.mockResolvedValue({ rows: [receipt('ga_primary')] })

    expect((await loadChartCapabilityOverlay(duplicateBindingContractSnapshot(), 'chart-1')).availability[0])
      .toMatchObject({ state: 'dark', available_binding_ids: [] })
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

  it('does not let one reviewed editorial route receipt enable another route binding in the generated snapshot', async () => {
    const generatedSnapshot = getPinnedCapabilityKnowledgeSnapshot()
    const source = generatedSnapshot.scus.find((scu) => scu.scu_id === 'scu.bodha.mechanism.network')!
    const sourceContract = source.availability_contracts![0]!
    const sourceRequirement = sourceContract.requirements.find((requirement) => requirement.kind === 'producer_output')!
    const targetBindingIds = [
      'scu.catalog.get_divisionals',
      'scu.finance.prosperity_assessment',
      'scu.yoga.firing_and_cancellation',
    ].flatMap((scuId) => generatedSnapshot.scus.find((scu) => scu.scu_id === scuId)!
      .bindings.filter((binding) => binding.executable).map((binding) => binding.binding_id))

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
