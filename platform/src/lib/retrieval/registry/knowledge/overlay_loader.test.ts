import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { CapabilityKnowledgeSnapshot } from './types'

const mocks = vi.hoisted(() => ({ query: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: mocks.query }))

import { loadChartCapabilityOverlay } from './overlay_loader'

const claimHash = 'a'.repeat(64)
const snapshot = {
  schema_version: '1.0.0', compatibility_version: 'planner-scu-v1', generated_at: '2026-09-13T00:00:00.000Z',
  content_hash: 'sha256:content', source_catalog_fingerprint: 'sha256:catalog', edges: [],
  census: { runtime_descriptors: 1, addressable_descriptors: 1, excluded_descriptors: 0, semantic_capabilities: 1, editorial_scus: 1, derived_scus: 0, executable_bindings: 1, unavailable_bindings: 0, publicly_named_bindings: 0, reviewed_pagination_bindings: 0, producer_output_claims: 1, reviewed_output_claims: 1, exclusions: [] },
  scus: [{
    scu_id: 'scu.test', version: 1, label: 'Test', description: 'Test', kind: 'datum', domains: ['all'], concepts: [], intents: [], horizons: ['natal'], scope: 'chart', inputs: [], outputs: [],
    primary_binding_uri: 'marsys://tool/L1/test', provenance_requirements: [], freshness_policy: 'fresh', entitlement: 'native', safety_notes: [], known_gaps: [], editorial: true,
    producer_output_claims: [{ asset_id: 'ga_test', component: 'rows', output_digest_spec_sha256: claimHash, disposition: 'reviewed_output', evidence: 'fixture' }],
    bindings: [{ binding_id: 'registry:marsys://tool/L1/test', kind: 'registry_capability', relation: 'primary', capability_uri: 'marsys://tool/L1/test', input_contract: {}, output_contract: {}, pagination: 'none', executable: true }],
    source_descriptor_uris: ['marsys://tool/L1/test'],
  }],
} as CapabilityKnowledgeSnapshot

beforeEach(() => {
  vi.clearAllMocks()
})

describe('chart capability overlay loader', () => {
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

  it('fails closed when a proven receipt belongs to a superseded build', async () => {
    mocks.query.mockResolvedValue({ rows: [{
      active_build_id: 'build-2', active_build_status: 'completed',
      asset_id: 'ga_test', chart_id: 'chart-1', build_id: 'build-1', receipt_version: 'v1', receipt_state: 'proven',
      output_digest_spec_sha256: claimHash, observed_at: '2026-09-13T00:00:00Z', freshness_state: 'fresh', unknown_reasons: [], freshness_reasons: [],
    }] })
    expect((await loadChartCapabilityOverlay(snapshot, 'chart-1')).availability[0]).toMatchObject({ state: 'incompatible', available_binding_ids: [] })
  })
})
