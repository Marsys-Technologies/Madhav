/**
 * SS N-356 — assess_* end to end: the KP cusp chain is read in the KRISHNAMURTI frame and
 * labelled, while the rest of the answer (sensitive-degree leg, domain stage) still reads Lahiri.
 * Both ayanamsha params are asserted in ONE query trace. Sub-capabilities are mocked at their
 * dynamic-import specifiers (pattern of register_d8_assess_domain.lane_e.test.ts).
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

const queryMock = vi.fn()
vi.mock('@/lib/db/client', () => ({ query: (...args: unknown[]) => queryMock(...args) }))
vi.mock('../../generation/served_generation', async (importOriginal) => {
  const original = await importOriginal<typeof import('../../generation/served_generation')>()
  return {
    ...original,
    resolveChartServedGeneration: async (chartId: string) => original.chartServedGenerationFromRows(chartId, null, [{
      asset_id: 'ga_structural', partition_key: '__whole_asset__', receipt_version: 'v1',
      receipt_build_id: '11111111-1111-4111-8111-111111111111', rows_build_id: '11111111-1111-4111-8111-111111111111',
      receipt_state: 'proven', freshness_state: 'fresh', output_digest_spec_sha256: 'a'.repeat(64), spec_active: true,
      receipt_run_state: 'completed', receipt_asset_present: true, receipt_disposition: 'build', observed_at: '2026-09-07T00:00:00Z',
    }]),
  }
})

const domainReadingHandler = vi.fn()
const temporalHandler = vi.fn()
const contradictionsHandler = vi.fn()
const signalsHandler = vi.fn()
const yogaFiringsHandler = vi.fn()
vi.mock('../L2_bodha/query_domain_reading', () => ({ queryDomainReadingCapability: { handler: (...a: unknown[]) => domainReadingHandler(...a) } }))
vi.mock('../L3_kala/query_temporal_activation', () => ({ queryTemporalActivationCapability: { handler: (...a: unknown[]) => temporalHandler(...a) } }))
vi.mock('../L2_bodha/query_contradictions', () => ({ queryContradictionsCapability: { handler: (...a: unknown[]) => contradictionsHandler(...a) } }))
vi.mock('../L2_bodha/query_signals', () => ({ querySignalsCapability: { handler: (...a: unknown[]) => signalsHandler(...a) } }))
vi.mock('../L1_ganita/get_yoga_firings', () => ({ getYogaFiringsCapability: { handler: (...a: unknown[]) => yogaFiringsHandler(...a) } }))
vi.mock('../../address_resolver', () => ({ resolveAddress: vi.fn().mockRejectedValue(new Error('no live DB in test')) }))

import { clearRegistry, getCapability } from '../../index'
import { registerD8AssessDomainCapabilities } from '../register_d8_assess_domain'
import { KP_FRAME_LABEL } from '@/lib/retrieval/kp_frame'
import { isKpChainRead, kpReadAyanamsha, kpRowsForHouses, recordedCalls } from './kp_chain_fixture'

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const LAHIRI = 'lahiri_chitrapaksha'
const SENSITIVE_CATEGORIES = ['pushkara', 'gandanta', 'mrityu_bhaga', 'kartari']

beforeEach(() => {
  queryMock.mockReset()
  queryMock.mockImplementation(async (sql: string, params: unknown[] = []) => {
    const s = String(sql)
    if (s.includes('brahma_vichara_constants')) {
      return { rows: [{ value_jsonb: {
        wealth: { vargas: ['D1', 'D2', 'D9', 'D11'], provisional: false, houses: [2, 11], karaka: 'Jupiter' },
        career: { vargas: ['D1', 'D10', 'D9'], provisional: true, houses: [10], karaka: 'Saturn' },
        marriage: { vargas: ['D1', 'D9', 'D7'], provisional: true, houses: [7], karaka: 'Venus' },
        health: { vargas: ['D1', 'D6', 'D9'], provisional: true, houses: [6], karaka: 'Saturn' },
        general: { vargas: ['D1', 'D9'], provisional: true, houses: [1], karaka: 'Sun' },
      } }] }
    }
    if (params.some(p => Array.isArray(p) && p.includes('cusp_kp_lords'))) return { rows: kpRowsForHouses([2, 11, 10, 7, 6, 1, 5, 9, 4, 8, 12, 3]) }
    return { rows: [] }
  })
  for (const h of [domainReadingHandler, temporalHandler, contradictionsHandler, signalsHandler, yogaFiringsHandler]) h.mockReset()
  domainReadingHandler.mockResolvedValue({ is_error: false, content: { question_lenses: [], signal_id_refs: [], cdlm_cells: [], lens_count: 0 } })
  temporalHandler.mockResolvedValue({ is_error: false, content: { activations: [], predicates: [], activation_count: 0, signal_id_refs: [] } })
  contradictionsHandler.mockResolvedValue({ is_error: false, content: { contradiction_count: 0, discoveries: [] } })
  signalsHandler.mockResolvedValue({ is_error: false, content: { signals: [], ranking_basis: { mode: 'composite_4d', priors_version: '1.2', domain: 'wealth' } } })
  yogaFiringsHandler.mockResolvedValue({ is_error: false, content: { rows: [] } })
})

describe('assess_*: KP chain at Krishnamurti, the rest at Lahiri', () => {
  it.each([
    ['assess_wealth', 'marsys://tool/L-DOMAIN/assess_wealth'],
    ['assess_career', 'marsys://tool/L-DOMAIN/assess_career'],
  ])('%s with the Lahiri primary id', async (_name, uri) => {
    clearRegistry()
    registerD8AssessDomainCapabilities()
    const cap = getCapability(uri)
    expect(cap).toBeDefined()
    const res = await cap!.handler({ chart_id: CHART_ID, ayanamsha_id: LAHIRI }, undefined)
    expect(res.is_error).toBe(false)
    const content = res.content as Record<string, unknown>

    // One trace carries both frames.
    const calls = recordedCalls(queryMock)
    const kpReads = calls.filter(isKpChainRead)
    expect(kpReads).toHaveLength(1)
    expect(kpReadAyanamsha(kpReads[0]!)).toBe('krishnamurti')
    expect(kpReads.some(c => c.params.includes(LAHIRI))).toBe(false)
    const sensitive = calls.filter(c => c.params.some(p => Array.isArray(p) && SENSITIVE_CATEGORIES.every(x => (p as unknown[]).includes(x))))
    expect(sensitive.length).toBeGreaterThan(0)
    for (const c of sensitive) expect(c.params[1]).toBe(LAHIRI)
    // The rest of the answer is still Lahiri: the sub-capabilities were handed the Lahiri id.
    const stageArgs = [domainReadingHandler, temporalHandler, signalsHandler].flatMap(h => h.mock.calls.map(c => c[0] as Record<string, unknown>))
    expect(stageArgs.length).toBeGreaterThan(0)
    expect(stageArgs.some(a => a['ayanamsha_id'] === LAHIRI)).toBe(true)
    expect(stageArgs.some(a => a['ayanamsha_id'] === 'krishnamurti')).toBe(false)

    // Served output: the labelled chain.
    const kp = content['kp_cusp_chain'] as Record<string, unknown>
    expect(kp['frame_label']).toBe(KP_FRAME_LABEL)
    expect(kp['ayanamsha_id']).toBe('krishnamurti')
    expect(String(kp['note'])).toContain(KP_FRAME_LABEL)
    expect((kp['cusps'] as unknown[]).length).toBeGreaterThan(0)

    const rc = content['reading_checklist'] as { units: Array<Record<string, unknown>> }
    const unit = rc.units.find(u => u['unit'] === 'kp_cusp_chain')!
    expect(unit['state']).toBe('served')
    expect(String(unit['detail'])).toContain(KP_FRAME_LABEL)
  })
})
