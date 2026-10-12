/**
 * SS N-356 — judgment_query end to end: the KP cusp chain is read in the KRISHNAMURTI frame and
 * labelled, while the rest of the answer (here the sensitive-degree leg) still reads Lahiri.
 * Both ayanamsha params are asserted in ONE query trace. DB, served generation and address
 * resolution are stubbed (same pattern as register_d9_judgment.wealth_leg_tiers.test.ts).
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'

const queryMock = vi.fn()
vi.mock('@/lib/db/client', () => ({ query: (...a: unknown[]) => queryMock(...a) }))

vi.mock('../reading_checklist', async (orig) => {
  const actual = await orig<typeof import('../reading_checklist')>()
  return {
    ...actual,
    fetchWealthReadingSourceFence: async () => ({ ok: true, ready: true, assets: [] }),
    fetchTajakaSourceFence: async () => ({ ok: true, ready: true, assets: [] }),
    fetchNotablyAbsentYogas: async () => actual.unprovenBand('test_stub'),
  }
})

vi.mock('../../generation/served_generation', async (orig) => {
  const actual = await orig<typeof import('../../generation/served_generation')>()
  const B = '11111111-1111-4111-8111-111111111111'
  const assets = ['ga_positions', 'ga_yoga', 'ga_dashas', 'ga_structural']
  return {
    ...actual,
    resolveChartServedGeneration: async (id: string) => actual.chartServedGenerationFromRows(id, null, assets.map(asset_id => ({
      asset_id, partition_key: '__whole_asset__', receipt_version: 'v1', receipt_build_id: B, rows_build_id: B,
      receipt_state: 'proven', freshness_state: 'fresh', output_digest_spec_sha256: 'a'.repeat(64), spec_active: true,
      receipt_run_state: 'completed', receipt_asset_present: true, receipt_disposition: 'build',
      observed_at: '2026-09-07T00:00:00Z',
    }))),
  }
})

vi.mock('../../../address_resolver', async (orig) => {
  const actual = await orig<typeof import('../../../address_resolver')>()
  return {
    ...actual,
    resolveAddress: async (_c: string, addr: { type: string; house?: number; frame?: string; graha?: string }) => {
      if (addr.type === 'bhava') return { entities: [{ kind: 'sign', sign: 'Taurus', house_number: addr.house, frame: addr.frame ?? 'lagna', fact_ids: ['f-sign'] }] }
      if (addr.type === 'lord_of') return { entities: [{ kind: 'graha', graha: 'Venus', graha_code: 'VEN', sign: 'Scorpio', house: 8, varga: 'D1', fact_ids: ['f-ven'] }] }
      if (addr.type === 'occupants_of') return { entities: [{ kind: 'occupants', house: addr.house, sign: 'Taurus', varga: 'D1', frame: 'lagna', grahas: [], fact_ids: ['f-occ'] }] }
      return { entities: [{ kind: 'graha', graha: addr.graha, graha_code: 'JUP', sign: 'Sagittarius', house: 9, varga: 'D1', fact_ids: ['f-k'] }] }
    },
  }
})

import { judgmentQueryCapability } from '../register_d9_judgment'
import { KP_FRAME_LABEL } from '@/lib/retrieval/kp_frame'
import { isKpChainRead, kpReadAyanamsha, kpRowsForHouses, recordedCalls } from './kp_chain_fixture'

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const LAHIRI = 'lahiri_chitrapaksha'
const SENSITIVE_CATEGORIES = ['pushkara', 'gandanta', 'mrityu_bhaga', 'kartari']

beforeEach(() => {
  queryMock.mockReset()
  queryMock.mockImplementation(async (sql: string, params: unknown[] = []) => {
    const t = String(sql)
    if (t.includes('brahma_vichara_constants')) {
      return { rows: [{ value_jsonb: {
        wealth: { vargas: ['D1', 'D9', 'D11'], operative: 'D9' }, career: { vargas: ['D1', 'D10'] },
        marriage: { vargas: ['D1', 'D9'] }, health: { vargas: ['D1'] }, general: { vargas: ['D1'] } } }] }
    }
    if (params.some(p => Array.isArray(p) && p.includes('cusp_kp_lords'))) return { rows: kpRowsForHouses([2, 11]) }
    return { rows: [] }
  })
})

describe('judgment_query: KP chain at Krishnamurti, the rest at Lahiri', () => {
  it.each([
    ['ayanamsha omitted (Lahiri default)', {}],
    ['explicit Lahiri', { ayanamsha_id: LAHIRI }],
  ])('%s', async (_name, extra) => {
    const r = await judgmentQueryCapability.handler({ chart_id: CHART_ID, domain: 'wealth', ...extra }, undefined)
    expect(r.is_error, JSON.stringify(r.content).slice(0, 300)).toBe(false)
    const content = r.content as Record<string, unknown>

    // One trace carries both frames.
    const calls = recordedCalls(queryMock)
    const kpReads = calls.filter(isKpChainRead)
    expect(kpReads).toHaveLength(1)
    expect(kpReadAyanamsha(kpReads[0]!)).toBe('krishnamurti')
    const sensitive = calls.filter(c => c.params.some(p => Array.isArray(p) && SENSITIVE_CATEGORIES.every(x => (p as unknown[]).includes(x))))
    expect(sensitive.length).toBeGreaterThan(0)
    for (const c of sensitive) expect(c.params[1]).toBe(LAHIRI)
    // No KP-category read ever carries the Lahiri id.
    expect(kpReads.some(c => c.params.includes(LAHIRI))).toBe(false)

    // Served output: the labelled chain.
    const checklist = content['checklist'] as Record<string, unknown> | undefined
    const kp = (content['kp_cusp_chain'] ?? checklist?.['kp_cusp_chain']) as Record<string, unknown> | undefined
    expect(kp, 'kp_cusp_chain slot').toBeDefined()
    expect(kp!['frame_label']).toBe(KP_FRAME_LABEL)
    expect(kp!['ayanamsha_id']).toBe('krishnamurti')
    expect(String(kp!['note'])).toContain(KP_FRAME_LABEL)
    expect((kp!['cusps'] as unknown[]).length).toBe(2)

    const rc = content['reading_checklist'] as { units: Array<Record<string, unknown>> }
    const unit = rc.units.find(u => u['unit'] === 'kp_cusp_chain')!
    expect(unit['state']).toBe('served')
    expect(String(unit['detail'])).toContain(KP_FRAME_LABEL)
  })
})
