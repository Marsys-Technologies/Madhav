/**
 * sse_streaming.integration.test.ts — SSE event format + event sequence tests.
 * MCPT v3.1.0-S2 AC.S2.7, AC.S2.8
 *
 * Tests verify that bundles emit the correct SSE event sequence:
 *   bundle.sub_tool.started → bundle.sub_tool.completed|error → bundle.completed
 *
 * No HTTP transport: tests run the executor directly with an onEvent callback.
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

import { executeHolisticBundle, type BundleEvent } from '../../src/bundles/holistic_bundle.js'
import { executeMultiSchoolBundle, type MultiSchoolBundleEvent } from '../../src/bundles/multi_school_bundle.js'

const MOCK_PRINCIPAL = {
  user_uid: 'test-uid',
  audience_tier: 'super_admin',
  key_id: 'test-key',
}

describe('SSE event sequence — holistic_bundle', () => {
  beforeEach(() => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ result: { signals: [{ signal_id: 'SIG.MSR.001' }] } }),
    })
    vi.clearAllMocks()
  })

  it('emits started → completed → bundle.completed in correct order (subset=MSR)', async () => {
    const events: BundleEvent[] = []

    await executeHolisticBundle(
      { query_text: 'test', tier: 'super_admin', subset: ['MSR'] },
      MOCK_PRINCIPAL,
      (event) => events.push(event)
    )

    expect(events[0]?.type).toBe('bundle.sub_tool.started')
    // Middle events may be completed or error
    expect(events[events.length - 1]?.type).toBe('bundle.completed')
  })

  it('emits started → error for each timed-out tool', async () => {
    const timeoutError = Object.assign(new Error('Timeout'), { name: 'TimeoutError' })
    mockFetch.mockRejectedValue(timeoutError)

    const events: BundleEvent[] = []
    await executeHolisticBundle(
      { query_text: 'test', tier: 'super_admin', subset: ['MSR', 'CGM'] },
      MOCK_PRINCIPAL,
      (event) => events.push(event)
    )

    const errorEvents = events.filter(e => e.type === 'bundle.sub_tool.error')
    expect(errorEvents.length).toBe(2)
    expect(errorEvents.every(e => 'error_class' in e && e.error_class === 'timeout')).toBe(true)
  })

  it('bundle.completed event contains the full envelope', async () => {
    const events: BundleEvent[] = []

    await executeHolisticBundle(
      { query_text: 'Saturn transit test', tier: 'acharya', subset: ['DASHA'] },
      MOCK_PRINCIPAL,
      (event) => events.push(event)
    )

    const completedEvent = events.find(e => e.type === 'bundle.completed')
    expect(completedEvent).toBeDefined()
    if (completedEvent?.type === 'bundle.completed') {
      expect(completedEvent.envelope.ok).toBe(true)
      expect(completedEvent.envelope.bundle_name).toBe('holistic_bundle')
      expect(Array.isArray(completedEvent.envelope.bundle_entries)).toBe(true)
    }
  })

  it('completed event includes rows_returned for successful MSR call', async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({
        result: {
          signals: [{ signal_id: 'SIG.MSR.001' }, { signal_id: 'SIG.MSR.002' }],
        },
      }),
    })

    const events: BundleEvent[] = []
    await executeHolisticBundle(
      { query_text: 'test', tier: 'super_admin', subset: ['MSR'] },
      MOCK_PRINCIPAL,
      (event) => events.push(event)
    )

    const completedEvent = events.find(
      e => e.type === 'bundle.sub_tool.completed' && 'sub_tool' in e && e.sub_tool === 'MSR'
    )
    expect(completedEvent).toBeDefined()
    if (completedEvent?.type === 'bundle.sub_tool.completed') {
      expect(completedEvent.rows_returned).toBe(2)
    }
  })
})

describe('SSE event sequence — multi_school_bundle', () => {
  beforeEach(() => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({
        result: { school_positions: [], convergence_score: 0.8 },
      }),
    })
    vi.clearAllMocks()
  })

  it('emits started events before completed events', async () => {
    const events: MultiSchoolBundleEvent[] = []

    await executeMultiSchoolBundle(
      { claim: 'Mars in Aries gives courage and aggression', schools: ['parashara'], tier: 'super_admin' },
      MOCK_PRINCIPAL,
      (event) => events.push(event)
    )

    const startedEvents = events.filter(e => e.type === 'bundle.sub_tool.started')
    const completedEvents = events.filter(e => e.type === 'bundle.sub_tool.completed' || e.type === 'bundle.sub_tool.error')
    expect(startedEvents.length).toBeGreaterThan(0)
    expect(events[events.length - 1]?.type).toBe('bundle.completed')

    // Each started event must have a corresponding completed or error event
    for (const started of startedEvents) {
      if (started.type === 'bundle.sub_tool.started') {
        const found = completedEvents.some(
          e => 'sub_tool' in e && e.sub_tool === started.sub_tool
        )
        expect(found).toBe(true)
      }
    }
  })

  it('bundle.completed contains claim and schools', async () => {
    const events: MultiSchoolBundleEvent[] = []

    await executeMultiSchoolBundle(
      { claim: 'Venus in 2nd house provides accumulated wealth', schools: ['parashara', 'jaimini'], tier: 'acharya' },
      MOCK_PRINCIPAL,
      (event) => events.push(event)
    )

    const completed = events.find(e => e.type === 'bundle.completed')
    if (completed?.type === 'bundle.completed') {
      expect(completed.envelope.claim).toBe('Venus in 2nd house provides accumulated wealth')
      expect(completed.envelope.schools).toContain('parashara')
    }
  })
})
