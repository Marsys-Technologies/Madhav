import { describe, it, expect, vi, beforeEach } from 'vitest'
import type { MsrSignal } from '@/lib/db/types'

// Mock storage and telemetry before importing the module under test
vi.mock('@/lib/storage', () => ({
  getStorageClient: vi.fn(),
}))

vi.mock('@/lib/telemetry', () => ({
  telemetry: { recordLatency: vi.fn() },
}))

import { getStorageClient } from '@/lib/storage'
import { tool } from '../msr_sql'
import type { QueryPlan } from '../types'

const mockQuery = vi.fn()

const baseSignal: MsrSignal = {
  signal_id: 'sig-001',
  native_id: 'abhisek_mohanty',
  domain: 'career',
  planet: 'Saturn',
  house: 10,
  nakshatra: 'Pushya',
  dasha_lord: 'Saturn',
  confidence: 0.85,
  significance: 0.9,
  is_forward_looking: false,
  claim_text: 'Saturn in 10th gives career obstacles that eventually yield',
  classical_basis: 'Brihat Parashara Hora Shastra',
  falsifier: 'No career disruption before 35',
  source_file: '025_HOLISTIC_SYNTHESIS/MSR_v3_0.md',
  source_version: '3.0',
  ingested_at: '2026-04-01T00:00:00Z',
}

const basePlan: QueryPlan = {
  query_plan_id: '00000000-0000-0000-0000-000000000001',
  query_text: 'Tell me about career',
  query_class: 'interpretive',
  domains: [],
  forward_looking: false,
  audience_tier: 'client',
  tools_authorized: ['msr_sql'],
  history_mode: 'synthesized',
  panel_mode: false,
  expected_output_shape: 'single_answer',
  manifest_fingerprint: 'abc123',
  schema_version: '1.0',
}

beforeEach(() => {
  vi.clearAllMocks()
  vi.mocked(getStorageClient).mockReturnValue({
    query: mockQuery,
    transaction: vi.fn(),
    readObject: vi.fn(),
    writeObject: vi.fn(),
    objectExists: vi.fn(),
    readFile: vi.fn(),
    fileExists: vi.fn(),
    listFiles: vi.fn(),
  })
})

describe('msr_sql tool', () => {
  it('returns a ToolBundle with valid structure', async () => {
    mockQuery.mockResolvedValue({ rows: [baseSignal], rowCount: 1 })

    const bundle = await tool.retrieve(basePlan)

    expect(bundle.tool_name).toBe('msr_sql')
    expect(bundle.tool_version).toBe('1.0.0')
    expect(bundle.schema_version).toBe('1.0')
    expect(bundle.served_from_cache).toBe(false)
    expect(bundle.cache_key).toBeUndefined()
    expect(typeof bundle.tool_bundle_id).toBe('string')
    expect(typeof bundle.latency_ms).toBe('number')
    expect(bundle.result_hash).toMatch(/^sha256:[0-9a-f]{64}$/)
    expect(bundle.results).toHaveLength(1)
    expect(bundle.results[0].content).toBe(baseSignal.claim_text)
    expect(bundle.results[0].source_canonical_id).toBe('MSR')
    expect(bundle.results[0].signal_id).toBe('sig-001')
    expect(bundle.results[0].confidence).toBe(0.85)
    expect(bundle.results[0].significance).toBe(0.9)
  })

  it('filters by domain: passes domain array to SQL', async () => {
    mockQuery.mockResolvedValue({ rows: [baseSignal], rowCount: 1 })

    const plan: QueryPlan = { ...basePlan, domains: ['career', 'health'] }
    await tool.retrieve(plan)

    const callArgs = mockQuery.mock.calls[0]
    // $2 param should be the domain array
    expect(callArgs[1][1]).toEqual(['career', 'health'])
  })

  it('passes null domain param when no domains specified', async () => {
    mockQuery.mockResolvedValue({ rows: [], rowCount: 0 })

    await tool.retrieve(basePlan)

    const callArgs = mockQuery.mock.calls[0]
    expect(callArgs[1][1]).toBeNull()
  })

  it('filters by planet: passes planet array to SQL', async () => {
    mockQuery.mockResolvedValue({ rows: [baseSignal], rowCount: 1 })

    const plan: QueryPlan = { ...basePlan, planets: ['Saturn', 'Jupiter'] }
    await tool.retrieve(plan)

    const callArgs = mockQuery.mock.calls[0]
    // $3 param should be the planet array
    expect(callArgs[1][2]).toEqual(['Saturn', 'Jupiter'])
  })

  it('passes null planet param when no planets specified', async () => {
    mockQuery.mockResolvedValue({ rows: [], rowCount: 0 })

    await tool.retrieve(basePlan)

    const callArgs = mockQuery.mock.calls[0]
    expect(callArgs[1][2]).toBeNull()
  })

  it('handles empty result gracefully', async () => {
    mockQuery.mockResolvedValue({ rows: [], rowCount: 0 })

    const bundle = await tool.retrieve(basePlan)

    expect(bundle.results).toHaveLength(0)
    expect(bundle.schema_version).toBe('1.0')
    expect(bundle.result_hash).toMatch(/^sha256:/)
  })

  it('sets forward_looking filter to true when plan.forward_looking is true', async () => {
    mockQuery.mockResolvedValue({ rows: [], rowCount: 0 })

    const plan: QueryPlan = { ...basePlan, forward_looking: true }
    await tool.retrieve(plan)

    const callArgs = mockQuery.mock.calls[0]
    // $4 param should be true
    expect(callArgs[1][3]).toBe(true)
  })

  it('passes native_id override from params', async () => {
    mockQuery.mockResolvedValue({ rows: [], rowCount: 0 })

    await tool.retrieve(basePlan, { native_id: 'other_native' })

    const callArgs = mockQuery.mock.calls[0]
    expect(callArgs[1][0]).toBe('other_native')
  })

  it('uses default native_id abhisek_mohanty when no override', async () => {
    mockQuery.mockResolvedValue({ rows: [], rowCount: 0 })

    await tool.retrieve(basePlan)

    const callArgs = mockQuery.mock.calls[0]
    expect(callArgs[1][0]).toBe('abhisek_mohanty')
  })

  // AC.11 — new filter params tests

  it('AC.11.1: signal_type filter passed as $6 param', async () => {
    mockQuery.mockResolvedValue({ rows: [], rowCount: 0 })

    await tool.retrieve(basePlan, { signal_type: ['yoga', 'aspect'] })

    const callArgs = mockQuery.mock.calls[0]
    expect(callArgs[1][5]).toEqual(['yoga', 'aspect'])
  })

  it('AC.11.2: temporal_activation filter passed as $7 param', async () => {
    mockQuery.mockResolvedValue({ rows: [], rowCount: 0 })

    await tool.retrieve(basePlan, { temporal_activation: ['natal-permanent'] })

    const callArgs = mockQuery.mock.calls[0]
    expect(callArgs[1][6]).toEqual(['natal-permanent'])
  })

  it('AC.11.3: valence filter passed as $8 param', async () => {
    mockQuery.mockResolvedValue({ rows: [], rowCount: 0 })

    await tool.retrieve(basePlan, { valence: ['benefic', 'mixed'] })

    const callArgs = mockQuery.mock.calls[0]
    expect(callArgs[1][7]).toEqual(['benefic', 'mixed'])
  })

  it('AC.11.4: backward compat — no new filters → $6-$9 all null', async () => {
    mockQuery.mockResolvedValue({ rows: [baseSignal], rowCount: 1 })

    await tool.retrieve(basePlan)

    const callArgs = mockQuery.mock.calls[0]
    expect(callArgs[1][5]).toBeNull()
    expect(callArgs[1][6]).toBeNull()
    expect(callArgs[1][7]).toBeNull()
    expect(callArgs[1][8]).toBeNull()
  })

  it('AC.11.5: entities_involved_any filter passed as $9 param', async () => {
    mockQuery.mockResolvedValue({ rows: [], rowCount: 0 })

    await tool.retrieve(basePlan, { entities_involved_any: ['PLN.SATURN', 'HSE.7'] })

    const callArgs = mockQuery.mock.calls[0]
    expect(callArgs[1][8]).toEqual(['PLN.SATURN', 'HSE.7'])
  })

  it('AC.11.6: filter values are passed as parameterized array (SQL injection safe)', async () => {
    mockQuery.mockResolvedValue({ rows: [], rowCount: 0 })

    const maliciousInput = ["'; DROP TABLE msr_signals; --"]
    await tool.retrieve(basePlan, { signal_type: maliciousInput })

    const callArgs = mockQuery.mock.calls[0]
    // Value is passed as a parameter array, never interpolated into the SQL string
    expect(callArgs[1][5]).toEqual(maliciousInput)
    // The SQL string itself should not contain the malicious value
    const sqlString = callArgs[0] as string
    expect(sqlString).not.toContain('DROP TABLE')
  })

  // D.2 — finance/wealth domain confidence_floor default
  it('D.2: finance domain uses 0.35 confidence_floor by default (not 0.6)', async () => {
    mockQuery.mockResolvedValue({ rows: [baseSignal], rowCount: 1 })

    const plan: QueryPlan = { ...basePlan, domains: ['finance'] }
    await tool.retrieve(plan)

    const callArgs = mockQuery.mock.calls[0]
    // $5 (index 4) = confidence_floor
    expect(callArgs[1][4]).toBe(0.35)
  })

  it('D.2: wealth domain uses 0.35 confidence_floor by default', async () => {
    mockQuery.mockResolvedValue({ rows: [], rowCount: 0 })

    const plan: QueryPlan = { ...basePlan, domains: ['wealth'] }
    await tool.retrieve(plan)

    const callArgs = mockQuery.mock.calls[0]
    expect(callArgs[1][4]).toBe(0.35)
  })

  it('D.2: non-finance domain still uses 0.6 confidence_floor', async () => {
    mockQuery.mockResolvedValue({ rows: [], rowCount: 0 })

    const plan: QueryPlan = { ...basePlan, domains: ['career'] }
    await tool.retrieve(plan)

    const callArgs = mockQuery.mock.calls[0]
    expect(callArgs[1][4]).toBe(0.6)
  })

  it('D.2: explicit confidence_floor overrides domain-specific default for finance', async () => {
    mockQuery.mockResolvedValue({ rows: [], rowCount: 0 })

    const plan: QueryPlan = { ...basePlan, domains: ['finance'] }
    await tool.retrieve(plan, { confidence_floor: 0.5 })

    const callArgs = mockQuery.mock.calls[0]
    // Explicit 0.5 should win over the 0.35 domain default
    expect(callArgs[1][4]).toBe(0.5)
  })

  // FIX-2 regression: forward_looking reads from params first, plan second
  describe('FIX-2 regression: params.forward_looking overrides plan.forward_looking', () => {
    it('params.forward_looking=true passes true to SQL $4 (even when plan.forward_looking=false)', async () => {
      mockQuery.mockResolvedValue({ rows: [], rowCount: 0 })

      // plan.forward_looking = false but params says true
      const plan: QueryPlan = { ...basePlan, forward_looking: false }
      await tool.retrieve(plan, { forward_looking: true })

      const callArgs = mockQuery.mock.calls[0]
      // $4 (index 3) = forward_looking filter in SQL
      expect(callArgs[1][3]).toBe(true)
    })

    it('params.forward_looking=false passes null to SQL $4 (no filter = all signals)', async () => {
      mockQuery.mockResolvedValue({ rows: [], rowCount: 0 })

      const plan: QueryPlan = { ...basePlan, forward_looking: true }
      await tool.retrieve(plan, { forward_looking: false })

      const callArgs = mockQuery.mock.calls[0]
      // params.forward_looking=false means "no filter" — pass null
      expect(callArgs[1][3]).toBeNull()
    })

    it('no params.forward_looking falls back to plan.forward_looking=true → passes true to SQL $4', async () => {
      mockQuery.mockResolvedValue({ rows: [], rowCount: 0 })

      const plan: QueryPlan = { ...basePlan, forward_looking: true }
      await tool.retrieve(plan)  // no params

      const callArgs = mockQuery.mock.calls[0]
      expect(callArgs[1][3]).toBe(true)
    })

    it('no params.forward_looking and plan.forward_looking=false → passes null to SQL $4', async () => {
      mockQuery.mockResolvedValue({ rows: [], rowCount: 0 })

      const plan: QueryPlan = { ...basePlan, forward_looking: false }
      await tool.retrieve(plan)  // no params

      const callArgs = mockQuery.mock.calls[0]
      expect(callArgs[1][3]).toBeNull()
    })
  })

  // FIX-7 regression: invocation_params.forward_looking logs actual SQL filter value, not plan.forward_looking
  describe('FIX-7 regression: invocation_params.forward_looking = actual SQL filter value', () => {
    it('when params.forward_looking=true, bundle.invocation_params.forward_looking is true', async () => {
      mockQuery.mockResolvedValue({ rows: [], rowCount: 0 })

      const plan: QueryPlan = { ...basePlan, forward_looking: false }
      const bundle = await tool.retrieve(plan, { forward_looking: true })

      // FIX-7: the bundle must log what was actually sent to SQL, not plan.forward_looking
      expect(bundle.invocation_params.forward_looking).toBe(true)
    })

    it('when params.forward_looking=false, bundle.invocation_params.forward_looking is null', async () => {
      mockQuery.mockResolvedValue({ rows: [], rowCount: 0 })

      const plan: QueryPlan = { ...basePlan, forward_looking: true }
      const bundle = await tool.retrieve(plan, { forward_looking: false })

      // params.forward_looking=false → null SQL filter; log should reflect null
      expect(bundle.invocation_params.forward_looking).toBeNull()
    })

    it('when plan.forward_looking=true and no params, bundle.invocation_params.forward_looking is true', async () => {
      mockQuery.mockResolvedValue({ rows: [], rowCount: 0 })

      const plan: QueryPlan = { ...basePlan, forward_looking: true }
      const bundle = await tool.retrieve(plan)

      expect(bundle.invocation_params.forward_looking).toBe(true)
    })
  })
})
