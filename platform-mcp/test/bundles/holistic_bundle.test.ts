/**
 * holistic_bundle.test.ts — Unit tests for holistic bundle composition.
 * MCPT v3.1.0-S2 AC.S2.1, AC.S2.2, AC.S2.6
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { computeCacheKey } from '../../src/bundles/cache.js'

// ── Mock cache module ─────────────────────────────────────────────────────────

vi.mock('../../src/bundles/cache.js', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../../src/bundles/cache.js')>()
  return {
    ...actual,
    cacheLookup: vi.fn().mockResolvedValue({ hit: false }),
    cacheStore: vi.fn().mockResolvedValue(undefined),
  }
})

// ── Mock fetch ────────────────────────────────────────────────────────────────

const mockFetch = vi.fn()
vi.stubGlobal('fetch', mockFetch)

// ── Import after mocks ────────────────────────────────────────────────────────

import { executeHolisticBundle } from '../../src/bundles/holistic_bundle.js'

const MOCK_PRINCIPAL = {
  user_uid: 'test-uid',
  audience_tier: 'super_admin',
  key_id: 'test-key',
}

function makePrimitiveResponse(data: unknown = { result: { signals: [], count: 0 } }) {
  return {
    ok: true,
    json: () => Promise.resolve(data),
  }
}

describe('executeHolisticBundle', () => {
  beforeEach(() => {
    mockFetch.mockResolvedValue(makePrimitiveResponse())
    vi.clearAllMocks()
  })

  it('fires all 8 sub-tools when no subset specified', async () => {
    mockFetch.mockResolvedValue(makePrimitiveResponse())

    const result = await executeHolisticBundle(
      { query_text: 'test query', tier: 'super_admin' },
      MOCK_PRINCIPAL
    )

    expect(result.ok).toBe(true)
    expect(result.bundle_name).toBe('holistic_bundle')
    expect(result.bundle_entries.length).toBe(8)
  })

  it('respects subset filter (case-insensitive)', async () => {
    mockFetch.mockResolvedValue(makePrimitiveResponse())

    const result = await executeHolisticBundle(
      { query_text: 'test', tier: 'super_admin', subset: ['MSR', 'dasha'] },
      MOCK_PRINCIPAL
    )

    const names = result.bundle_entries.map(e => e.sub_tool)
    expect(names).toContain('MSR')
    expect(names).toContain('DASHA')
    expect(result.bundle_entries.length).toBe(2)
  })

  it('error-isolates: tool error produces errored slot, not bundle failure', async () => {
    // All tools error
    mockFetch.mockRejectedValue(new Error('Network error'))

    const result = await executeHolisticBundle(
      { query_text: 'test', tier: 'super_admin' },
      MOCK_PRINCIPAL
    )

    expect(result.ok).toBe(true) // bundle itself succeeds
    expect(result.bundle_entries.every(e => e.errored)).toBe(true)
    expect(result.provenance.sub_tools_errored.length).toBe(8)
    expect(result.provenance.sub_tools_fired.length).toBe(0)
  })

  it('collects signal_ids from successful MSR results', async () => {
    const msrResponse = {
      result: {
        signals: [
          { signal_id: 'SIG.MSR.001' },
          { signal_id: 'SIG.MSR.002' },
        ],
      },
    }
    mockFetch
      .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(msrResponse) })
      .mockResolvedValue(makePrimitiveResponse())

    const result = await executeHolisticBundle(
      { query_text: 'test', tier: 'super_admin', subset: ['MSR'] },
      MOCK_PRINCIPAL
    )

    expect(result.provenance.signal_ids_available).toContain('SIG.MSR.001')
    expect(result.provenance.signal_ids_available).toContain('SIG.MSR.002')
  })

  it('sets served_from_cache: false on fresh results', async () => {
    mockFetch.mockResolvedValue(makePrimitiveResponse())

    const result = await executeHolisticBundle(
      { query_text: 'fresh query', tier: 'super_admin' },
      MOCK_PRINCIPAL
    )

    expect(result.served_from_cache).toBe(false)
  })

  it('emits onEvent for each sub-tool start, complete, and bundle.completed', async () => {
    mockFetch.mockResolvedValue(makePrimitiveResponse())

    const events: string[] = []
    await executeHolisticBundle(
      { query_text: 'test', tier: 'super_admin', subset: ['MSR'] },
      MOCK_PRINCIPAL,
      (event) => { events.push(event.type) }
    )

    expect(events).toContain('bundle.sub_tool.started')
    expect(events).toContain('bundle.completed')
  })
})

describe('computeCacheKey (integration with holistic params)', () => {
  it('same params produce same key', () => {
    const params = {
      bundleName: 'holistic_bundle',
      queryText: 'Saturn dasha career',
      compositionParams: { subset: ['MSR', 'CGM'] },
      tier: 'acharya',
      chartId: 'test-chart',
    }
    expect(computeCacheKey(params)).toBe(computeCacheKey(params))
  })
})
