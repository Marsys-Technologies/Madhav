/**
 * register_d9_judgment.near_miss.test.ts -- consumer behaviour of the NMB-CAND-v1 serve-time
 * formation band (packet v1.0 as narrowed by v1.2: no near_miss state).
 *
 * Runs the REAL judgment_query handler with the DB, the served generation and address
 * resolution stubbed and `fetchNotablyAbsentYogas` replaced by canned results, so the tests pin
 * what the handler DOES with each band state: the checklist unit, the served (empty) array, the
 * retired/kept `notably_absent_not_checked` flag, exhaustiveness and the band block. The band
 * fetcher itself is covered in reading_checklist.near_miss.test.ts.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'

const queryMock = vi.fn()
vi.mock('@/lib/db/client', () => ({ query: (...a: unknown[]) => queryMock(...a) }))

const bandMock = vi.fn()
vi.mock('../reading_checklist', async (orig) => ({
  ...(await orig<typeof import('../reading_checklist')>()),
  fetchNotablyAbsentYogas: (...a: unknown[]) => bandMock(...a),
}))

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
import {
  interpretYogaBandResponse,
  unprovenBand,
} from '../reading_checklist'

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const AYA = 'lahiri_chitrapaksha'
const BUILD = '11111111-1111-4111-8111-111111111111'
const IDS = ['dhana_yoga_house_lords', 'dhana_yoga_2_11', 'dhana_yoga_5_9', 'dhana_yoga_lagna_2', 'dhana_yoga_9_11', 'dhana_yoga_2_5_9_11']

function cand(id: string, state: string) {
  return {
    candidate_id: id, yoga_name: `Dhana ${id}`, formation_text: `Lords associate (${id}).`, state,
    reason: state === 'indeterminate' ? 'no_l1_firing_rows_seen' : null, pairs: [], l1_firing_ids: [],
    constituent_fact_ids: [`fact-${id}`], contradicting_present_siblings: [], overlaps: [],
  }
}
function band(states: Record<string, string> = {}, aya = AYA): unknown {
  return {
    band_version: 'NMB-BAND-v1', candidate_set_version: 'NMB-CAND-v1', eligibility_rule_version: 'NMB-ELIG-v1',
    tolerance: 'none', chart_id: CHART_ID, ayanamsha_id: aya, served_build_ids: [BUILD],
    candidates: IDS.map(id => cand(id, states[id] ?? 'absent')),
  }
}
const interpret = (states: Record<string, string>, others: Array<{ ayanamsha_id: string; raw: unknown | null }> = []) =>
  interpretYogaBandResponse(band(states), { chart_id: CHART_ID, ayanamsha_id: AYA, served_build_ids: [BUILD] }, others)

beforeEach(() => {
  queryMock.mockReset()
  bandMock.mockReset()
  queryMock.mockImplementation(async (sql: string) => {
    if (String(sql).includes('brahma_vichara_constants')) {
      return { rows: [{ value_jsonb: {
        wealth: { vargas: ['D1', 'D9', 'D11'], operative: 'D9' }, career: { vargas: ['D1', 'D10'] },
        marriage: { vargas: ['D1', 'D9'] }, health: { vargas: ['D1'] }, general: { vargas: ['D1'] } } }] }
    }
    return { rows: [] }
  })
})

interface Checklist {
  notably_absent_yogas: Array<Record<string, unknown>>
  notably_absent_yogas_band: Record<string, unknown> | null
}

async function run(domain: string) {
  const r = await judgmentQueryCapability.handler({ chart_id: CHART_ID, domain }, undefined)
  expect(r.is_error, JSON.stringify(r.content).slice(0, 300)).toBe(false)
  const c = r.content as Record<string, unknown>
  const rc = c['reading_checklist'] as { units: Array<Record<string, unknown>> }
  const units = new Map(rc.units.map(u => [u['unit'] as string, u]))
  const flags = (c['judgment_flags'] as Array<Record<string, unknown>>).map(f => f['code'])
  return { c, rc, unit: units.get('notably_absent_yogas') as Record<string, unknown>, flags, checklist: c['checklist'] as Checklist }
}

describe('judgment_query notably-absent yogas -- consumer behaviour (packet v1.2)', () => {
  it('serves an empty array with band_coverage, near_miss_capable_candidates 0 and the not-claimed note; never not_computed', async () => {
    bandMock.mockResolvedValue(interpret({ dhana_yoga_2_11: 'present' }))
    const { unit, flags, checklist } = await run('wealth')
    expect(unit.state).toBe('empty_for_this_chart')
    expect(unit.state).not.toBe('not_computed')
    expect(unit.count).toBe(0)
    expect(checklist.notably_absent_yogas).toEqual([])
    const b = checklist.notably_absent_yogas_band!
    expect(b['band_coverage']).toEqual({ present: 1, near_miss: 0, absent: 5, indeterminate: 0, total: 6 })
    expect(b['near_miss_capable_candidates']).toBe(0)
    expect(b['formation_gap_detection']).toBe('not_claimed')
    expect(String(b['note'])).toMatch(/formation-gap detection is not claimed/i)
    expect(String(unit.detail)).toMatch(/not claimed/i)
    expect(b['candidate_set_version']).toBe('NMB-CAND-v1')
    expect(String(b['overlap_note'])).toMatch(/yoga count/)
    expect(flags).not.toContain('notably_absent_not_checked')
    expect(bandMock).toHaveBeenCalledTimes(1)
    expect(bandMock.mock.calls[0]!.slice(0, 2)).toEqual([CHART_ID, AYA])
  })

  it('never emits a near_miss row or state anywhere in the response', async () => {
    bandMock.mockResolvedValue(interpret({ dhana_yoga_2_11: 'present', dhana_yoga_5_9: 'indeterminate' }))
    const { c } = await run('wealth')
    const json = JSON.stringify(c)
    expect(json).not.toMatch(/"state":"near_miss"/)
    expect(json).not.toMatch(/Not formed:/)
  })

  it('B1: an indeterminate candidate makes the unit source_unproven (band_indeterminate) and the read non-exhaustive', async () => {
    bandMock.mockResolvedValue(interpret({ dhana_yoga_5_9: 'indeterminate' }))
    const { unit, flags, checklist, rc } = await run('wealth')
    expect(unit.state).toBe('source_unproven')
    expect(String(unit.detail)).toContain('band_indeterminate')
    expect(checklist.notably_absent_yogas_band!['state']).toBe('source_unproven')
    expect(checklist.notably_absent_yogas_band!['reason']).toBe('band_indeterminate')
    expect(checklist.notably_absent_yogas_band!['indeterminate']).toEqual([{ candidate_id: 'dhana_yoga_5_9', reason: 'no_l1_firing_rows_seen' }])
    expect(flags).toContain('notably_absent_not_checked')
    const exh = (rc as unknown as { exhaustive: boolean }).exhaustive
    expect(exh).toBe(false)
    expect(((rc as unknown as { units_unserved: string[] }).units_unserved)).toContain('notably_absent_yogas')
  })

  it.each(['sidecar_unavailable', 'band_rows_incomplete:5/6', 'generation_unresolved', 'ayanamsha_not_canonical'])(
    'source_unproven (%s): never not_computed, never an empty finding, flag kept with the reason', async (reason) => {
      bandMock.mockResolvedValue(unprovenBand(reason))
      const { unit, flags, checklist } = await run('wealth')
      expect(unit.state).toBe('source_unproven')
      expect(unit.state).not.toBe('not_computed')
      expect(unit.detail).toContain(reason)
      expect(checklist.notably_absent_yogas).toEqual([])
      expect(checklist.notably_absent_yogas_band!['state']).toBe('source_unproven')
      expect(flags).toContain('notably_absent_not_checked')
    })

  it('non-wealth domains do not read the band and report not_joined (flag kept)', async () => {
    const { unit, flags, checklist } = await run('marriage')
    expect(bandMock).not.toHaveBeenCalled()
    expect(unit.state).toBe('not_joined')
    expect(unit.state).not.toBe('not_computed')
    expect(checklist.notably_absent_yogas).toEqual([])
    expect(checklist.notably_absent_yogas_band).toBeNull()
    expect(flags).toContain('notably_absent_not_checked')
  })

  it('B2: surfaces ayanamsha sensitivity as true / false / null exactly as the fetcher result says', async () => {
    const differs = interpret({ dhana_yoga_2_11: 'present' }, [{ ayanamsha_id: 'raman', raw: band({}, 'raman') }])
    bandMock.mockResolvedValue(differs)
    let r = await run('wealth')
    expect(r.checklist.notably_absent_yogas_band!['ayanamsha_sensitive']).toBe(true)
    expect(r.checklist.notably_absent_yogas_band!['ayanamsha_sensitive_candidates']).toEqual(['dhana_yoga_2_11'])

    bandMock.mockResolvedValue(interpret({}, [{ ayanamsha_id: 'raman', raw: band({}, 'raman') }]))
    r = await run('wealth')
    expect(r.checklist.notably_absent_yogas_band!['ayanamsha_sensitive']).toBe(false)

    bandMock.mockResolvedValue(interpret({}, []))
    r = await run('wealth')
    expect(r.checklist.notably_absent_yogas_band!['ayanamsha_sensitive']).toBeNull()
    expect(String(r.checklist.notably_absent_yogas_band!['ayanamsha_sensitivity_note'])).toMatch(/no neighbouring ayanamsha/i)
  })

  it('folds the band constituent fact ids into the receipt fact refs', async () => {
    bandMock.mockResolvedValue(interpret({ dhana_yoga_2_11: 'present' }))
    const { c } = await run('wealth')
    expect(JSON.stringify(c['fact_id_refs'])).toContain('fact-dhana_yoga_2_11')
  })
})
