/**
 * register_d9_judgment.near_miss.test.ts -- consumer behaviour of the NMB-CAND-v1 serve-time
 * formation band (packet v1.0 section 6/7 as amended by v1.1).
 *
 * Runs the REAL judgment_query handler with the DB, the served generation and address
 * resolution stubbed and `fetchNotablyAbsentYogas` replaced by canned results, so the tests pin
 * what the handler DOES with each band state: the checklist unit, the served array, the
 * retired/kept `notably_absent_not_checked` flag and the band block. The band fetcher itself is
 * covered in reading_checklist.near_miss.test.ts.
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
  NEAR_MISS_FORBIDDEN_WORDING,
  interpretYogaBandResponse,
  unprovenBand,
  type NotablyAbsentYogasResult,
} from '../reading_checklist'

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const AYA = 'lahiri_chitrapaksha'
const BUILD = '11111111-1111-4111-8111-111111111111'
const IDS = ['dhana_yoga_house_lords', 'dhana_yoga_2_11', 'dhana_yoga_5_9', 'dhana_yoga_lagna_2', 'dhana_yoga_9_11', 'dhana_yoga_2_5_9_11']

function cand(id: string, state: string, extra: Record<string, unknown> = {}) {
  return {
    candidate_id: id, yoga_name: id === 'dhana_yoga_house_lords' ? 'Dhana Yoga (House-Lord Family)' : `Dhana ${id}`,
    formation_text: id === 'dhana_yoga_house_lords'
      ? 'Any association among the lords of houses 1/2/5/9/11 where the pair includes the 2nd or 11th lord, and the meeting house is not a dusthana (6/8/12).'
      : `Lords associate (${id}).`,
    state, reason: state === 'near_miss' ? 'gate_only_failure:association_in_dusthana' : null, pairs: [], l1_firing_ids: [],
    constituent_fact_ids: [], contradicting_present_siblings: [], ...extra,
  }
}
function band(states: Record<string, string> = {}): unknown {
  return {
    band_version: 'NMB-BAND-v1', candidate_set_version: 'NMB-CAND-v1', eligibility_rule_version: 'NMB-ELIG-v1',
    tolerance: 'none', chart_id: CHART_ID, ayanamsha_id: AYA, served_build_ids: [BUILD],
    candidates: IDS.map(id => cand(id, states[id] ?? 'absent', id === 'dhana_yoga_house_lords' && states[id] === 'near_miss'
      ? {
        pairs: [{ houses_ruled: [2, 11], lords: ['venus', 'saturn'], association_mode: 'conjunction', placement_houses: [8], associated: true, gate_failed: true }],
        constituent_fact_ids: ['fact-b', 'fact-a'], contradicting_present_siblings: ['dhana_yoga_2_11'],
      } : {})),
  }
}
const interpret = (states: Record<string, string>) =>
  interpretYogaBandResponse(band(states), { chart_id: CHART_ID, ayanamsha_id: AYA, served_build_ids: [BUILD] })

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
  return { c, unit: units.get('notably_absent_yogas') as Record<string, unknown>, flags, checklist: c['checklist'] as Checklist }
}

describe('judgment_query notably-absent yogas -- consumer behaviour', () => {
  it('serves near_miss rows only, unit served with count == array length, flag retired, wording clean', async () => {
    bandMock.mockResolvedValue(interpret({ dhana_yoga_house_lords: 'near_miss', dhana_yoga_2_11: 'present', dhana_yoga_5_9: 'indeterminate' }))
    const { unit, flags, checklist } = await run('wealth')
    const rows = checklist.notably_absent_yogas
    expect(unit.state).toBe('served')
    expect(unit.count).toBe(rows.length)
    expect(rows).toHaveLength(1)
    expect(rows.every(r => r.state === 'near_miss')).toBe(true)
    expect(rows[0].statement).toMatch(/^Not formed: Dhana Yoga \(House-Lord Family\) requires /)
    expect(rows[0].statement).toContain('it fails the meeting-house leg')
    expect(rows[0].statement).not.toMatch(NEAR_MISS_FORBIDDEN_WORDING)
    expect(rows[0].contradicting_present_siblings).toEqual(['dhana_yoga_2_11'])
    expect(rows[0].constituent_fact_ids).toEqual(['fact-a', 'fact-b'])
    const b = checklist.notably_absent_yogas_band!
    expect(b['band_coverage']).toEqual({ present: 1, near_miss: 1, absent: 3, indeterminate: 1, total: 6 })
    expect(b['indeterminate']).toEqual([{ candidate_id: 'dhana_yoga_5_9', reason: null }])
    expect(b['candidate_set_version']).toBe('NMB-CAND-v1')
    expect(flags).not.toContain('notably_absent_not_checked')
    expect(bandMock).toHaveBeenCalledTimes(1)
    expect(bandMock.mock.calls[0]!.slice(0, 2)).toEqual([CHART_ID, AYA])
  })

  it('empty_for_this_chart when the band is proven and holds zero near_miss rows (flag retired)', async () => {
    bandMock.mockResolvedValue(interpret({ dhana_yoga_2_11: 'present' }))
    const { unit, flags, checklist } = await run('wealth')
    expect(unit.state).toBe('empty_for_this_chart')
    expect(unit.count).toBe(0)
    expect(checklist.notably_absent_yogas).toEqual([])
    expect((checklist.notably_absent_yogas_band!['band_coverage'] as { total: number }).total).toBe(6)
    expect(flags).not.toContain('notably_absent_not_checked')
  })

  it.each(['bo_laksana_missing_fence', 'sidecar_unavailable', 'band_rows_incomplete:5/6', 'generation_unresolved'])(
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

  it('surfaces ayanamsha sensitivity and indeterminate candidates from the fetcher result', async () => {
    const res: NotablyAbsentYogasResult = interpretYogaBandResponse(
      band({ dhana_yoga_house_lords: 'near_miss' }),
      { chart_id: CHART_ID, ayanamsha_id: AYA, served_build_ids: [BUILD] },
      [{ ayanamsha_id: 'raman', raw: { ...(band({ dhana_yoga_house_lords: 'present' }) as object), ayanamsha_id: 'raman' } }],
    )
    bandMock.mockResolvedValue(res)
    const { checklist } = await run('wealth')
    const b = checklist.notably_absent_yogas_band!
    expect(b['ayanamsha_sensitive']).toBe(true)
    expect(b['ayanamsha_sensitive_candidates']).toEqual(['dhana_yoga_house_lords'])
    expect(checklist.notably_absent_yogas[0]!['ayanamsha_sensitive']).toBe(true)
  })

  it('folds near-miss constituent fact ids into the receipt fact refs', async () => {
    bandMock.mockResolvedValue(interpret({ dhana_yoga_house_lords: 'near_miss' }))
    const { c } = await run('wealth')
    expect(JSON.stringify(c['fact_id_refs'])).toContain('fact-a')
  })
})
