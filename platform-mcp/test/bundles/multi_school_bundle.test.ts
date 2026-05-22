/**
 * multi_school_bundle.test.ts — Unit tests for multi_school_bundle.
 * MCPT v3.1.0-S2 AC.S2.3, AC.S2.4
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'

// ── Mock cache module ─────────────────────────────────────────────────────────

vi.mock('../../src/bundles/cache.js', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../../src/bundles/cache.js')>()
  return {
    ...actual,
    cacheLookup: vi.fn().mockResolvedValue({ hit: false }),
    cacheStore: vi.fn().mockResolvedValue(undefined),
  }
})

const mockFetch = vi.fn()
vi.stubGlobal('fetch', mockFetch)

import { executeMultiSchoolBundle } from '../../src/bundles/multi_school_bundle.js'

const MOCK_PRINCIPAL = {
  user_uid: 'test-uid',
  audience_tier: 'acharya',
  key_id: 'test-key',
}

function makeOkResponse(data: unknown = { result: { school_positions: [], convergence_score: 0.75 } }) {
  return { ok: true, json: () => Promise.resolve(data) }
}

describe('executeMultiSchoolBundle', () => {
  beforeEach(() => {
    mockFetch.mockResolvedValue(makeOkResponse())
    vi.clearAllMocks()
  })

  it('fires cross_school_lookup + 4 per-school tasks by default', async () => {
    const result = await executeMultiSchoolBundle(
      { claim: 'Saturn in 10th house delays career until 36', tier: 'acharya' },
      MOCK_PRINCIPAL
    )

    expect(result.ok).toBe(true)
    expect(result.bundle_name).toBe('multi_school_bundle')
    // 1 cross_school_lookup + 4 per-school (parashara, jaimini, kp, tajaka) = 5 minimum
    expect(result.bundle_entries.length).toBeGreaterThanOrEqual(5)
    const subToolNames = result.bundle_entries.map(e => e.sub_tool)
    expect(subToolNames).toContain('cross_school_lookup')
    expect(subToolNames.some(n => n.includes('parashara'))).toBe(true)
  })

  it('respects schools subset filter', async () => {
    const result = await executeMultiSchoolBundle(
      {
        claim: 'Moon-Ketu conjunction in 4th house indicates maternal separation theme',
        schools: ['parashara', 'jaimini'],
        tier: 'super_admin',
      },
      MOCK_PRINCIPAL
    )

    const subToolNames = result.bundle_entries.map(e => e.sub_tool)
    expect(subToolNames.some(n => n.includes('kp'))).toBe(false)
    expect(subToolNames.some(n => n.includes('tajaka'))).toBe(false)
    expect(subToolNames.some(n => n.includes('parashara'))).toBe(true)
    expect(subToolNames.some(n => n.includes('jaimini'))).toBe(true)
  })

  it('error-isolates: tool errors produce errored slots, not bundle failure', async () => {
    mockFetch.mockRejectedValue(new Error('Network error'))

    const result = await executeMultiSchoolBundle(
      { claim: 'Saturn aspects 7th lord damages partnerships', tier: 'acharya' },
      MOCK_PRINCIPAL
    )

    expect(result.ok).toBe(true) // bundle succeeds despite tool errors
    expect(result.provenance.sub_tools_errored.length).toBeGreaterThan(0)
  })

  it('stores claim and schools in the envelope', async () => {
    const claim = 'Venus in 8th house challenges longevity'
    const schools = ['parashara', 'kp'] as const

    const result = await executeMultiSchoolBundle(
      { claim, schools: [...schools], tier: 'super_admin' },
      MOCK_PRINCIPAL
    )

    expect(result.claim).toBe(claim)
    expect(result.schools).toContain('parashara')
    expect(result.schools).toContain('kp')
  })

  it('emits bundle.completed event via onEvent callback', async () => {
    const events: string[] = []

    await executeMultiSchoolBundle(
      { claim: 'Rahu in 10th house amplifies ambition', tier: 'acharya' },
      MOCK_PRINCIPAL,
      (event) => { events.push(event.type) }
    )

    expect(events).toContain('bundle.completed')
  })

  it('served_from_cache is false on fresh results', async () => {
    const result = await executeMultiSchoolBundle(
      { claim: 'Mars in Aries 1st house grants courage', tier: 'super_admin' },
      MOCK_PRINCIPAL
    )
    expect(result.served_from_cache).toBe(false)
  })
})
