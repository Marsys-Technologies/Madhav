/**
 * register_d10_pact.test.ts — pact_query chain-honesty unit tests (R5 W4, design §26/§28.3).
 * ==============================================================================================
 * DB-free (per the query_signals_paradigm.test.ts precedent): mocks `@/lib/db/client` and the
 * `judgment_query` capability it delegates PROMISE to, so the four-stage HALTING behavior is
 * exercised deterministically without a live chart. This is the concrete demonstration the R5
 * W4 lane asked for: "verify the denied-promise-halts-honestly behavior with a concrete example".
 *
 * Scope:
 *   1. PROMISE denied ('contested' verdict_grade) → pact_status='denied_at_promise', chain
 *      stops at ONE stage, CONFIRMATION/ACTIVATION/TRIGGER never attempted (no DB dignity call).
 *   2. PROMISE promised, CONFIRMATION denied (net-hostile varga dignity) → pact_status=
 *      'denied_at_confirmation', chain stops at TWO stages, ACTIVATION/TRIGGER never attempted.
 *   3. PROMISE + CONFIRMATION pass, ACTIVATION pending (future-only dasha window) → chain
 *      reports 'chain_pending_activation' HONESTLY (not a denial) and TRIGGER is 'not_yet',
 *      never fabricating a gate check against a window that has not opened.
 *   4. All four stages actually run and complete when every gate passes ('chain_complete').
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

const mockQuery = vi.fn()
vi.mock('@/lib/db/client', () => ({ query: (...args: unknown[]) => mockQuery(...args) }))

const mockJudgmentHandler = vi.fn()
vi.mock('../register_d9_judgment', () => ({
  judgmentQueryCapability: { handler: (...args: unknown[]) => mockJudgmentHandler(...args) },
}))

import { pactQueryCapability } from '../register_d10_pact'

function judgmentContent(overrides: Record<string, unknown> = {}) {
  return {
    chart_id: CHART_ID,
    ayanamsha_id: 'lahiri_chitrapaksha',
    about: { domain: 'marriage', bhava: 7, label: 'Marriage / Partnership', karakas: ['Venus'], operative_varga: 'D9' },
    verdict: { verdict_grade: 'convergent_strong', composite_score: 3.0 },
    receipt: { varga_confirmed: 'D9✓', bhanga_checked: false },
    checklist: {
      bhavesha_condition: { from_lagna: { graha: 'Venus' } },
      timing_hooks: { current: [], mahadasha_windows_by_graha: {} },
    },
    judgment_flags: [],
    fact_id_refs: ['f-1'],
    resolution_chains: {},
    ...overrides,
  }
}

beforeEach(() => {
  vi.unstubAllGlobals()
  mockQuery.mockReset()
  mockJudgmentHandler.mockReset()
})

describe('pact_query — Stage 1 PROMISE denial halts the chain (design §28.3)', () => {
  it('a contested verdict_grade halts at PROMISE — pact_status=denied_at_promise, ONE stage, no DB dignity query fired', async () => {
    mockJudgmentHandler.mockResolvedValue({
      is_error: false,
      content: judgmentContent({ verdict: { verdict_grade: 'contested', composite_score: -1.5 } }),
    })

    const result = await pactQueryCapability.handler({ chart_id: CHART_ID, domain: 'marriage' }, undefined)

    expect(result.is_error).toBe(false)
    const content = result.content as Record<string, unknown>
    expect(content['pact_status']).toBe('denied_at_promise')
    const stages = content['stages'] as Array<Record<string, unknown>>
    expect(stages).toHaveLength(1)
    expect(stages[0]!['stage']).toBe('PROMISE')
    expect(stages[0]!['status']).toBe('denied')

    // Chain honesty: CONFIRMATION never ran — no chart_facts dignity query was fired at all.
    expect(mockQuery).not.toHaveBeenCalled()

    const drillPointers = content['drill_pointers'] as Array<Record<string, unknown>>
    expect(drillPointers.some(p => p['pact_stage'] === 'promise')).toBe(true)

    const flags = content['judgment_flags'] as Array<{ code: string } | string>
    expect(flags.some(f => typeof f !== 'string' && f.code === 'pact_halted_at_promise')).toBe(true)
  })
})

describe('pact_query — Stage 2 CONFIRMATION denial halts the chain', () => {
  it('net-hostile D9 dignity for the bhāveśa halts at CONFIRMATION — pact_status=denied_at_confirmation, TWO stages, no dasha/transit calls', async () => {
    mockJudgmentHandler.mockResolvedValue({ is_error: false, content: judgmentContent() })
    // register_d10_pact's own gradeGrahaInVarga query — debilitated in D9 for Venus.
    mockQuery.mockResolvedValue({ rows: [{ fact_id: 'df-1', fact_value_text: 'debilitated' }] })

    const result = await pactQueryCapability.handler({ chart_id: CHART_ID, domain: 'marriage' }, undefined)

    const content = result.content as Record<string, unknown>
    expect(content['pact_status']).toBe('denied_at_confirmation')
    const stages = content['stages'] as Array<Record<string, unknown>>
    expect(stages).toHaveLength(2)
    expect(stages[1]!['stage']).toBe('CONFIRMATION')
    expect(stages[1]!['status']).toBe('denied')

    const flags = content['judgment_flags'] as Array<{ code: string } | string>
    expect(flags.some(f => typeof f !== 'string' && f.code === 'pact_halted_at_confirmation')).toBe(true)
  })

  it('a missing D9 dignity row is reported "inconclusive", NOT fabricated as a denial (B.10)', async () => {
    mockJudgmentHandler.mockResolvedValue({ is_error: false, content: judgmentContent() })
    mockQuery.mockResolvedValue({ rows: [] })

    const result = await pactQueryCapability.handler({ chart_id: CHART_ID, domain: 'marriage' }, undefined)
    const content = result.content as Record<string, unknown>
    const stages = content['stages'] as Array<Record<string, unknown>>
    const confirmation = stages.find(s => s['stage'] === 'CONFIRMATION')!
    expect(confirmation['status']).toBe('inconclusive')
    // inconclusive does NOT halt the chain — ACTIVATION still runs.
    expect(stages.some(s => s['stage'] === 'ACTIVATION')).toBe(true)
  })
})

describe('pact_query — Stage 3 ACTIVATION: pending vs. denied vs. active', () => {
  it('no current dasha but a future window exists → "pending", NOT denied; TRIGGER honestly reports not_yet', async () => {
    mockJudgmentHandler.mockResolvedValue({
      is_error: false,
      content: judgmentContent({
        checklist: {
          bhavesha_condition: { from_lagna: { graha: 'Venus' } },
          timing_hooks: {
            current: [],
            mahadasha_windows_by_graha: { Venus: [{ start_date: '2099-01-01', end_date: '2119-01-01' }] },
          },
        },
      }),
    })
    mockQuery.mockResolvedValue({ rows: [{ fact_id: 'df-2', fact_value_text: 'exalted' }] })

    const result = await pactQueryCapability.handler({ chart_id: CHART_ID, domain: 'marriage', as_of_date: '2026-07-08' }, undefined)
    const content = result.content as Record<string, unknown>
    expect(content['pact_status']).toBe('chain_pending_activation')
    const stages = content['stages'] as Array<Record<string, unknown>>
    expect(stages.map(s => s['stage'])).toEqual(['PROMISE', 'CONFIRMATION', 'ACTIVATION', 'TRIGGER'])
    expect(stages[2]!['status']).toBe('pending')
    expect(stages[3]!['status']).toBe('not_yet')
    // No fetch to the ephemeris sidecar fired — TRIGGER never attempted a real gate check.
  })

  it('no current AND no future dasha window at all → ACTIVATION denied ("no dasha can deliver it")', async () => {
    mockJudgmentHandler.mockResolvedValue({
      is_error: false,
      content: judgmentContent({
        checklist: {
          bhavesha_condition: { from_lagna: { graha: 'Venus' } },
          timing_hooks: { current: [], mahadasha_windows_by_graha: { Venus: [{ start_date: '1990-01-01', end_date: '2010-01-01' }] } },
        },
      }),
    })
    mockQuery.mockResolvedValue({ rows: [{ fact_id: 'df-3', fact_value_text: 'own' }] })

    const result = await pactQueryCapability.handler({ chart_id: CHART_ID, domain: 'marriage', as_of_date: '2026-07-08' }, undefined)
    const content = result.content as Record<string, unknown>
    expect(content['pact_status']).toBe('denied_at_activation')
    const stages = content['stages'] as Array<Record<string, unknown>>
    expect(stages).toHaveLength(3)
    expect(stages[2]!['reason']).toMatch(/no dasha can deliver it/)
  })
})

describe('pact_query — all four stages complete', () => {
  it('active-now dasha reaches TRIGGER but reports chain_incomplete_infra (R-22) when the sidecar is unreachable — never chain_complete for an unreached TRIGGER', async () => {
    mockJudgmentHandler.mockResolvedValue({
      is_error: false,
      content: judgmentContent({
        checklist: {
          bhavesha_condition: { from_lagna: { graha: 'Venus' } },
          timing_hooks: {
            current: [{ lord_graha: 'Venus', level_n: 1, start_date: '2020-01-01', end_date: '2040-01-01' }],
            mahadasha_windows_by_graha: { Venus: [{ start_date: '2020-01-01', end_date: '2040-01-01' }] },
          },
        },
      }),
    })
    mockQuery.mockResolvedValue({ rows: [{ fact_id: 'df-4', fact_value_text: 'exalted' }] })
    vi.stubGlobal('fetch', vi.fn(async () => ({ ok: false, status: 503, text: async () => 'unavailable' })))

    const result = await pactQueryCapability.handler({ chart_id: CHART_ID, domain: 'marriage', as_of_date: '2026-07-08' }, undefined)
    const content = result.content as Record<string, unknown>
    // R-22: TRIGGER was attempted but the sidecar was unreachable — this is an INFRA gap,
    // not a passed chain. pact_status must say so, not "chain_complete" (which previously
    // fired here regardless of whether TRIGGER data was ever actually fetched).
    expect(content['pact_status']).toBe('chain_incomplete_infra')
    const stages = content['stages'] as Array<Record<string, unknown>>
    expect(stages.map(s => s['stage'])).toEqual(['PROMISE', 'CONFIRMATION', 'ACTIVATION', 'TRIGGER'])
    expect(stages[2]!['status']).toBe('active_now')
    expect(stages[3]!['status']).toBe('unreachable')
    expect(String(stages[3]!['reason'])).toMatch(/honest gap, not fabricated/)
  })

  it('reports chain_complete only when TRIGGER data was actually fetched', async () => {
    mockJudgmentHandler.mockResolvedValue({
      is_error: false,
      content: judgmentContent({
        checklist: {
          bhavesha_condition: { from_lagna: { graha: 'Venus' } },
          timing_hooks: {
            current: [{ lord_graha: 'Venus', level_n: 1, start_date: '2020-01-01', end_date: '2040-01-01' }],
            mahadasha_windows_by_graha: { Venus: [{ start_date: '2020-01-01', end_date: '2040-01-01' }] },
          },
        },
      }),
    })
    mockQuery.mockResolvedValue({ rows: [{ fact_id: 'df-4', fact_value_text: 'exalted' }] })
    vi.stubGlobal('fetch', vi.fn(async () => ({
      ok: true, status: 200, json: async () => ({ rows: [{ longitude: 123.45 }] }),
    })))

    const result = await pactQueryCapability.handler({ chart_id: CHART_ID, domain: 'marriage', as_of_date: '2026-07-08' }, undefined)
    const content = result.content as Record<string, unknown>
    expect(content['pact_status']).toBe('chain_complete')
    const stages = content['stages'] as Array<Record<string, unknown>>
    expect(stages[3]!['status']).toBe('gate_data_fetched')
  })
})

describe('pact_query — input validation', () => {
  it('requires chart_id', async () => {
    const result = await pactQueryCapability.handler({ domain: 'marriage' }, undefined)
    expect(result.is_error).toBe(true)
  })

  it('requires domain or bhava', async () => {
    const result = await pactQueryCapability.handler({ chart_id: CHART_ID }, undefined)
    expect(result.is_error).toBe(true)
  })
})

// CR-40 regression: register_d10_pact.ts's TRIGGER stage predates the WP-1.7 x-api-key
// forwarding fix (query_planet_position.ts) by 4 days and was never brought onto it — the
// live symptom was pact_status='chain_incomplete_infra' even though the sidecar's
// /brahmagyan/ephemeris/planet_transit route was reachable and correct (confirmed live via
// the same route through l0_ephemeris.ts's sidecarGet, which DOES send the header). A missing
// or mismatched x-api-key 401s against verify_api_key whenever PYTHON_SIDECAR_API_KEY is set;
// this call's `if (res.ok)` check silently read that 401 as "no rows", indistinguishable from
// a genuinely unreachable sidecar. Module-level SIDECAR_API_KEY is read once at import, so this
// suite isolates the module with vi.resetModules() + a fresh dynamic import per case, after
// stubbing process.env, to exercise both the "key configured" and "no key configured" paths.
describe('pact_query — TRIGGER stage forwards the sidecar API key (CR-40)', () => {
  const activeNowJudgment = () => judgmentContent({
    checklist: {
      bhavesha_condition: { from_lagna: { graha: 'Venus' } },
      timing_hooks: {
        current: [{ lord_graha: 'Venus', level_n: 1, start_date: '2020-01-01', end_date: '2040-01-01' }],
        mahadasha_windows_by_graha: { Venus: [{ start_date: '2020-01-01', end_date: '2040-01-01' }] },
      },
    },
  })

  afterEach(() => {
    delete process.env['PYTHON_SIDECAR_API_KEY']
    vi.unstubAllGlobals()
  })

  it('sends x-api-key on the TRIGGER fetch when PYTHON_SIDECAR_API_KEY is configured', async () => {
    process.env['PYTHON_SIDECAR_API_KEY'] = 'test-sidecar-key'
    vi.resetModules()

    const fetchMock = vi.fn(async () => ({
      ok: true, status: 200, json: async () => ({ rows: [{ longitude: 123.45 }] }),
    }))
    vi.stubGlobal('fetch', fetchMock)

    mockJudgmentHandler.mockResolvedValue({ is_error: false, content: activeNowJudgment() })
    mockQuery.mockResolvedValue({ rows: [{ fact_id: 'df-4', fact_value_text: 'exalted' }] })

    const { pactQueryCapability: freshCapability } = await import('../register_d10_pact')
    const result = await freshCapability.handler(
      { chart_id: CHART_ID, domain: 'marriage', as_of_date: '2026-07-08' }, undefined,
    )
    const content = result.content as Record<string, unknown>
    expect(content['pact_status']).toBe('chain_complete')

    expect(fetchMock).toHaveBeenCalled()
    const [, requestInit] = fetchMock.mock.calls[0] as unknown as [string, { headers?: Record<string, string> }]
    expect(requestInit?.headers?.['x-api-key']).toBe('test-sidecar-key')
  })

  it('omits x-api-key entirely when PYTHON_SIDECAR_API_KEY is not configured (no fabricated header)', async () => {
    delete process.env['PYTHON_SIDECAR_API_KEY']
    vi.resetModules()

    const fetchMock = vi.fn(async () => ({
      ok: true, status: 200, json: async () => ({ rows: [{ longitude: 123.45 }] }),
    }))
    vi.stubGlobal('fetch', fetchMock)

    mockJudgmentHandler.mockResolvedValue({ is_error: false, content: activeNowJudgment() })
    mockQuery.mockResolvedValue({ rows: [{ fact_id: 'df-4', fact_value_text: 'exalted' }] })

    const { pactQueryCapability: freshCapability } = await import('../register_d10_pact')
    const result = await freshCapability.handler(
      { chart_id: CHART_ID, domain: 'marriage', as_of_date: '2026-07-08' }, undefined,
    )
    const content = result.content as Record<string, unknown>
    expect(content['pact_status']).toBe('chain_complete')

    expect(fetchMock).toHaveBeenCalled()
    const [, requestInit] = fetchMock.mock.calls[0] as unknown as [string, { headers?: Record<string, string> }]
    expect(requestInit?.headers?.['x-api-key']).toBeUndefined()
  })
})
