/**
 * register_d8_verdict_skeleton.test.ts — WP-1.3(i) / R-40 verdict_skeleton serving fixes
 * =======================================================================================
 * Root-cause (this run, against prod chart 482012f1-… on lahiri):
 *   - `lord` bucket keyed on signal_type_class='relationship' — a DOMAIN, never a class.
 *     ZERO signals carry that class → the bucket was permanently empty (serving bug).
 *   - `strength` bucket keyed on class='magnitude' + source_subsystem='strength_ashtakavarga'
 *     — neither value exists in bodha_msr_signals (graha strength is an L1 chart_facts
 *     concept, not an MSR signal class) → permanently empty (serving bug).
 *   - rare structural classes (configuration=29, yoga=15, parivartana=42, varga=9 chart-wide)
 *     were starved by slicing from the top-50 composite pool, which is ~82% composite_state.
 *   - `temporal` empties because kala_activation has NULL activation dates (native 0/13,364
 *     dated) — DATA-PLANE writer defect (R-45/R-40 shared root), owned by WP-2.1, NOT a
 *     serving bug. This test asserts it is DISCLOSED honestly, not faked.
 *
 * These tests mock the four sub-capabilities + the db client so they assert the serving-side
 * bucketing logic against controlled inputs (not live data).
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'

const queryMock = vi.fn()
vi.mock('@/lib/db/client', () => ({
  query: (...args: unknown[]) => queryMock(...args),
}))

const domainReadingHandler = vi.fn()
const temporalHandler = vi.fn()
const contradictionsHandler = vi.fn()
const signalsHandler = vi.fn()

vi.mock('../L2_bodha/query_domain_reading', () => ({
  queryDomainReadingCapability: { handler: (...a: unknown[]) => domainReadingHandler(...a) },
}))
vi.mock('../L3_kala/query_temporal_activation', () => ({
  queryTemporalActivationCapability: { handler: (...a: unknown[]) => temporalHandler(...a) },
}))
vi.mock('../L2_bodha/query_contradictions', () => ({
  queryContradictionsCapability: { handler: (...a: unknown[]) => contradictionsHandler(...a) },
}))
vi.mock('../L2_bodha/query_signals', () => ({
  querySignalsCapability: { handler: (...a: unknown[]) => signalsHandler(...a) },
}))

import { clearRegistry, getCapability } from '../../index'
import { registerD8AssessDomainCapabilities } from '../register_d8_assess_domain'

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

function sig(id: string, cls: string, sss = 'structural') {
  return {
    signal_id: id,
    signal_type_class: cls,
    source_subsystem: sss,
    signal_summary_text: `summary-${id}`,
    computed_salience: 0.5,
  }
}

beforeEach(() => {
  queryMock.mockReset()
  domainReadingHandler.mockReset()
  temporalHandler.mockReset()
  contradictionsHandler.mockReset()
  signalsHandler.mockReset()

  // domain reading OK, minimal content
  domainReadingHandler.mockResolvedValue({
    is_error: false,
    content: { question_lenses: [], signal_id_refs: [], cdlm_cells: [], lens_count: 0 },
  })
  // temporal returns NO activations (simulates the R-45 NULL-date data defect)
  temporalHandler.mockResolvedValue({
    is_error: false,
    content: { activations: [], predicates: [], activation_count: 0, signal_id_refs: [] },
  })
  // contradictions: zero rows for this chart
  contradictionsHandler.mockResolvedValue({
    is_error: false,
    content: { contradiction_count: 0, discoveries: [] },
  })
  // composite pool (top_10 source) — dominated by composite_state, as in prod
  signalsHandler.mockResolvedValue({
    is_error: false,
    content: {
      signals: Array.from({ length: 50 }, (_, i) => sig(`comp-${i}`, 'composite_state')),
      ranking_basis: { mode: 'composite', priors_version: '1.0', domain: 'career' },
    },
  })
  // stratified stage-pool query — returns the rare structural classes. F-164: routes the
  // brahma_vichara_constants read (DOMAIN_DIRECT_VARGAS is now a live read, not a literal)
  // to a realistic fixture rather than falling through to the structural-class rows below,
  // which are shaped nothing like {value_jsonb}.
  queryMock.mockImplementation(async (sql: string) => {
    if (String(sql).includes('brahma_vichara_constants')) {
      return {
        rows: [{
          value_jsonb: {
            wealth:   { vargas: ['D1', 'D2', 'D9', 'D11'], provisional: false, houses: [2, 11], karaka: 'Jupiter' },
            career:   { vargas: ['D1', 'D10', 'D9'], provisional: true, houses: [10], karaka: 'Saturn' },
            marriage: { vargas: ['D1', 'D9', 'D7'], provisional: true, houses: [7], karaka: 'Venus' },
            health:   { vargas: ['D1', 'D6', 'D9'], provisional: true, houses: [6], karaka: 'Saturn' },
            general:  { vargas: ['D1', 'D9'], provisional: true, houses: [1], karaka: 'Sun' },
          },
        }],
      }
    }
    return {
      rows: [
        sig('par-1', 'parivartana'),
        sig('par-2', 'parivartana'),
        sig('yog-1', 'yoga', 'yoga'),
        sig('cfg-1', 'configuration'),
        sig('kar-1', 'karaka_alignment'),
        sig('var-1', 'varga_pattern', 'varga'),
      ],
    }
  })
})

async function runCareer() {
  clearRegistry()
  registerD8AssessDomainCapabilities()
  const cap = getCapability('marsys://tool/L-DOMAIN/assess_career')
  expect(cap).toBeDefined()
  const res = await cap!.handler({ chart_id: CHART_ID }, undefined)
  expect(res.is_error).toBe(false)
  const content = res.content as Record<string, unknown>
  return content['verdict_skeleton'] as Record<string, unknown>
}

describe('WP-1.3(i) — verdict_skeleton lord bucket keyed to a REAL class (parivartana)', () => {
  it('populates lord from parivartana signals (was dead: keyed on non-existent "relationship")', async () => {
    const vs = await runCareer()
    const byStage = vs['by_stage'] as Record<string, unknown[]>
    expect(byStage['lord'].length).toBeGreaterThan(0)
    const ids = byStage['lord'].map((s) => (s as Record<string, unknown>)['signal_id'])
    expect(ids).toContain('par-1')
  })

  it('the stratified pool query restricts to stage-bearing classes incl. parivartana', async () => {
    await runCareer()
    const call = queryMock.mock.calls.find(([sql]) => String(sql).includes('bodha_msr_signals'))
    expect(call, 'expected a stratified stage-pool query').toBeDefined()
    const [sql, params] = call as [string, unknown[]]
    expect(sql).toMatch(/domains_affected_array/)
    const flat = JSON.stringify(params)
    expect(flat).toContain('parivartana')
    expect(flat).toContain('career')
  })
})

describe('WP-1.3(i) — rare structural stages no longer starved by the composite pool', () => {
  it('populates yoga and varga stages from the stratified pool', async () => {
    const vs = await runCareer()
    const byStage = vs['by_stage'] as Record<string, unknown[]>
    expect(byStage['yoga'].length).toBeGreaterThan(0)
    expect(byStage['varga'].length).toBeGreaterThan(0)
  })
})

describe('WP-1.3(i) — stage_status discloses provenance + honest empty reasons', () => {
  it('marks temporal empty as the R-45/WP-2.1 data-plane defect, NOT faked', async () => {
    const vs = await runCareer()
    const status = vs['stage_status'] as Record<string, Record<string, unknown>>
    expect(status).toBeDefined()
    expect(status['temporal']['count']).toBe(0)
    expect(String(status['temporal']['empty_reason'])).toMatch(/R-45|WP-2\.1|activation date|NULL/i)
  })

  it('marks strength as an L1 chart_facts concept (no MSR signal class), with a drill', async () => {
    const vs = await runCareer()
    const status = vs['stage_status'] as Record<string, Record<string, unknown>>
    const byStage = vs['by_stage'] as Record<string, unknown[]>
    expect(byStage['strength']).toEqual([])
    expect(String(status['strength']['source'])).toMatch(/L1|chart_facts|shadbala/i)
    expect(status['strength']['drill_uri']).toBeTruthy()
  })

  it('marks contradiction_pairs empty as no_data (0 bodha_contradictions), not a trim', async () => {
    const vs = await runCareer()
    const status = vs['stage_status'] as Record<string, Record<string, unknown>>
    expect(String(status['contradiction_pairs']['empty_reason'])).toMatch(/no_data|0 rows|contradiction/i)
  })
})
