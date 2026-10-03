/**
 * register_d9_judgment.wealth_leg_tiers.test.ts — TI-served-tier-legs, consumer side.
 *
 * Runs the REAL judgment_query handler (wealth) with the DB, the served generation and address
 * resolution stubbed (same pattern as register_d9_judgment.near_miss.test.ts), the two source
 * fences forced ready, and the three wealth legs REAL over a SQL-routed `query` mock. It pins what
 * the handler DOES with each leg state:
 *   - the checklist unit (`special_lagnas`, `yogi_avayogi`, `tajaka`) carries tier_breakdown /
 *     verified_count / evidence_tier when served, and incomplete_reason when source_incomplete;
 *   - the `checklist.wealth_*` response blocks always carry all four fields;
 *   - served-at-unverified-tier, incomplete (missing evidence), incomplete (unservable tier) and
 *     unproven are four distinct outcomes, never conflated.
 * The fetchers' own predicate is covered in reading_checklist.wealth_leg_tiers.test.ts.
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
import { WEALTH_SPECIAL_LAGNAS, WEALTH_SPECIAL_LAGNA_KEYS, WEALTH_YOGI_SUBJECT_KEYS } from '../reading_checklist'

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const NUMERIC_LAGNA_KEYS = new Set(['longitude_sidereal', 'pada', 'house_d1'])

const lagnaRows = (tier: string) => WEALTH_SPECIAL_LAGNAS.flatMap(subject => WEALTH_SPECIAL_LAGNA_KEYS.map(fact_key => ({
  fact_id: `${subject}-${fact_key}`, fact_subject: subject, fact_key,
  fact_value_num: NUMERIC_LAGNA_KEYS.has(fact_key) ? 12 : null,
  fact_value_text: NUMERIC_LAGNA_KEYS.has(fact_key) ? null : 'Aries',
  verification_pass_status: tier,
})))
const yogiRows = (tier: string) => Object.entries(WEALTH_YOGI_SUBJECT_KEYS).flatMap(([fact_subject, keys]) => keys.map(fact_key => ({
  fact_id: `${fact_subject}-${fact_key}`, fact_subject, fact_key,
  fact_value_num: fact_key === 'point_longitude' ? 123.45 : null,
  fact_value_text: fact_key === 'point_longitude' ? null : 'Mercury',
  verification_pass_status: tier,
})))
const tajakaRow = (tier: string) => ({
  varsha_id: 'annual-1', varsha_year: 42,
  varsha_start_iso: '2020-01-01T00:00:00.000Z', varsha_end_iso: '2100-01-01T00:00:00.000Z',
  year_lord_method: 'tajik_classical', year_lord: 'Jupiter',
  candidate_lord_jsonb: { Jupiter: 5 }, muntha_position_jsonb: { sign: 'Aries' },
  applicable_tajik_yogas_array: [], verification_pass_status: tier,
  citation_ref: 'tajaka-ref', citation_human: 'Tajaka citation.',
})

type LegData = { lagna: unknown[] | Error; yogi: unknown[] | Error; tajaka: unknown[] | Error }

function route(d: LegData) {
  queryMock.mockImplementation(async (sql: string) => {
    const t = String(sql)
    const out = (v: unknown[] | Error) => { if (v instanceof Error) throw v; return { rows: v } }
    if (t.includes('brahma_vichara_constants')) {
      return { rows: [{ value_jsonb: {
        wealth: { vargas: ['D1', 'D9', 'D11'], operative: 'D9' }, career: { vargas: ['D1', 'D10'] },
        marriage: { vargas: ['D1', 'D9'] }, health: { vargas: ['D1'] }, general: { vargas: ['D1'] } } }] }
    }
    if (t.includes("fact_category = 'special_lagna'")) return out(d.lagna)
    if (t.includes("fact_category = 'sensitive_point_yogi'")) return out(d.yogi)
    if (t.includes('FROM l1_tajik_varsha_year_lords')) return out(d.tajaka)
    return { rows: [] }
  })
}

beforeEach(() => queryMock.mockReset())

async function run() {
  const r = await judgmentQueryCapability.handler({ chart_id: CHART_ID, domain: 'wealth' }, undefined)
  expect(r.is_error, JSON.stringify(r.content).slice(0, 300)).toBe(false)
  const c = r.content as Record<string, unknown>
  const units = new Map((c['reading_checklist'] as { units: Array<Record<string, unknown>> }).units.map(u => [u['unit'] as string, u]))
  const checklist = c['checklist'] as Record<string, Record<string, unknown>>
  const rc = c['reading_checklist'] as Record<string, unknown>
  return {
    rc,
    unit: { lagna: units.get('special_lagnas')!, yogi: units.get('yogi_avayogi')!, tajaka: units.get('tajaka')! },
    block: { lagna: checklist['wealth_special_lagnas']!, yogi: checklist['wealth_yogi_avayogi']!, tajaka: checklist['wealth_tajaka']! },
  }
}

describe('judgment_query wealth legs — tier carriage into checklist units and response blocks', () => {
  it('served at a VERIFIED tier (today): count = verified_count, evidence_tier verified, no incomplete_reason', async () => {
    route({ lagna: lagnaRows('two_pass_verified'), yogi: yogiRows('two_pass_verified'), tajaka: [tajakaRow('two_pass_verified')] })
    const { unit, block } = await run()
    expect(unit.lagna).toMatchObject({ state: 'served', count: 21, tier_breakdown: { two_pass_verified: 21 }, verified_count: 21, evidence_tier: 'verified' })
    expect(unit.yogi).toMatchObject({ state: 'served', count: 12, tier_breakdown: { two_pass_verified: 12 }, verified_count: 12, evidence_tier: 'verified' })
    expect(unit.tajaka).toMatchObject({ state: 'served', count: 1, tier_breakdown: { two_pass_verified: 1 }, verified_count: 1, evidence_tier: 'verified' })
    for (const u of Object.values(unit)) expect(u).not.toHaveProperty('incomplete_reason')
    expect(block.lagna).toMatchObject({ state: 'served', tier_breakdown: { two_pass_verified: 21 }, verified_count: 21, evidence_tier: 'verified', incomplete_reason: null })
    expect(block.yogi).toMatchObject({ state: 'served', verified_count: 12, evidence_tier: 'verified', incomplete_reason: null })
    expect(block.tajaka).toMatchObject({ state: 'served', tier: 'two_pass_verified', verified_count: 1, evidence_tier: 'verified', incomplete_reason: null })
  })

  it('served at PRESENT-AT-UNVERIFIED-TIER (post S-L1: single / classical_match): served, verified_count 0, never source_incomplete', async () => {
    route({ lagna: lagnaRows('single'), yogi: yogiRows('classical_match'), tajaka: [tajakaRow('classical_match')] })
    const { unit, block } = await run()
    expect(unit.lagna).toMatchObject({ state: 'served', count: 21, tier_breakdown: { single: 21 }, verified_count: 0, evidence_tier: 'present_at_unverified_tier' })
    expect(unit.yogi).toMatchObject({ state: 'served', count: 12, tier_breakdown: { classical_match: 12 }, verified_count: 0, evidence_tier: 'present_at_unverified_tier' })
    expect(unit.tajaka).toMatchObject({ state: 'served', count: 1, tier_breakdown: { classical_match: 1 }, verified_count: 0, evidence_tier: 'present_at_unverified_tier' })
    for (const u of Object.values(unit)) expect(u).not.toHaveProperty('incomplete_reason')
    expect(block.lagna).toMatchObject({ state: 'served', verified_count: 0, evidence_tier: 'present_at_unverified_tier', incomplete_reason: null })
    expect(block.yogi).toMatchObject({ state: 'served', verified_count: 0, evidence_tier: 'present_at_unverified_tier', incomplete_reason: null })
    expect(block.tajaka).toMatchObject({ state: 'served', tier: 'classical_match', verified_count: 0, evidence_tier: 'present_at_unverified_tier', incomplete_reason: null })
    // every served row keeps its own tier in the response block
    expect((block.lagna['rows'] as Array<Record<string, unknown>>).every(r => r['verification_pass_status'] === 'single')).toBe(true)
    expect((block.yogi['rows'] as Array<Record<string, unknown>>).every(r => r['verification_pass_status'] === 'classical_match')).toBe(true)
  })

  it('source_incomplete / evidence_missing_or_malformed: reason on unit and block, no tier fields on the unit', async () => {
    route({ lagna: lagnaRows('single').slice(1), yogi: yogiRows('classical_match').slice(1), tajaka: [] })
    const { unit, block } = await run()
    for (const u of Object.values(unit)) {
      expect(u).toMatchObject({ state: 'source_incomplete', count: 0, incomplete_reason: 'evidence_missing_or_malformed' })
      expect(u).not.toHaveProperty('evidence_tier')
      expect(u).not.toHaveProperty('tier_breakdown')
    }
    for (const b of Object.values(block)) {
      expect(b).toMatchObject({ state: 'source_incomplete', verified_count: 0, evidence_tier: null, incomplete_reason: 'evidence_missing_or_malformed' })
    }
    expect(block.lagna['rows']).toEqual([])
    expect(block.tajaka['row']).toBeNull()
  })

  it('source_incomplete / unservable_tier (floored rows): a different reason from missing evidence', async () => {
    route({ lagna: lagnaRows('floored'), yogi: yogiRows('floored'), tajaka: [tajakaRow('floored')] })
    const { unit, block } = await run()
    for (const u of Object.values(unit)) {
      expect(u).toMatchObject({ state: 'source_incomplete', count: 0, incomplete_reason: 'unservable_tier' })
      expect(u).not.toHaveProperty('evidence_tier')
    }
    for (const b of Object.values(block)) {
      expect(b).toMatchObject({ state: 'source_incomplete', verified_count: 0, evidence_tier: null, incomplete_reason: 'unservable_tier' })
    }
  })

  it('source_unproven (failed read): no incomplete_reason anywhere, no tier fields on the unit', async () => {
    route({ lagna: new Error('db'), yogi: new Error('db'), tajaka: new Error('db') })
    const { unit, block } = await run()
    for (const u of Object.values(unit)) {
      expect(u).toMatchObject({ state: 'source_unproven', count: 0 })
      expect(u).not.toHaveProperty('incomplete_reason')
      expect(u).not.toHaveProperty('evidence_tier')
    }
    for (const b of Object.values(block)) {
      expect(b).toMatchObject({ state: 'source_unproven', verified_count: 0, evidence_tier: null, incomplete_reason: null })
    }
  })

  it('the four outcomes are pairwise distinct on (state, evidence_tier, incomplete_reason) for the special_lagnas unit', async () => {
    const triples: string[] = []
    for (const lagna of [lagnaRows('two_pass_verified'), lagnaRows('single'), lagnaRows('single').slice(1), lagnaRows('floored'), new Error('db')]) {
      route({ lagna, yogi: yogiRows('classical_match'), tajaka: [tajakaRow('classical_match')] })
      const { unit } = await run()
      triples.push(`${unit.lagna['state']}|${unit.lagna['evidence_tier'] ?? '-'}|${unit.lagna['incomplete_reason'] ?? '-'}`)
    }
    expect(triples).toEqual([
      'served|verified|-',
      'served|present_at_unverified_tier|-',
      'source_incomplete|-|evidence_missing_or_malformed',
      'source_incomplete|-|unservable_tier',
      'source_unproven|-|-',
    ])
  })

  it('units_served_unverified_tier counts served-but-not-verified wealth units (present_at_unverified_tier AND mixed), never verified/incomplete/unproven ones', async () => {
    const lagnaMixed = lagnaRows('single').map((r, i) => (i === 0 ? { ...r, verification_pass_status: 'two_pass_verified' } : r))
    const cases: Array<[string, LegData, number]> = [
      ['all verified', { lagna: lagnaRows('two_pass_verified'), yogi: yogiRows('two_pass_verified'), tajaka: [tajakaRow('two_pass_verified')] }, 0],
      ['all present at unverified tier', { lagna: lagnaRows('single'), yogi: yogiRows('classical_match'), tajaka: [tajakaRow('classical_match')] }, 3],
      ['one mixed unit + two verified', { lagna: lagnaMixed, yogi: yogiRows('two_pass_verified'), tajaka: [tajakaRow('two_pass_verified')] }, 1],
      ['incomplete (floored) legs', { lagna: lagnaRows('floored'), yogi: yogiRows('floored'), tajaka: [tajakaRow('floored')] }, 0],
      ['unproven legs', { lagna: new Error('db'), yogi: new Error('db'), tajaka: new Error('db') }, 0],
    ]
    const exhaustive: unknown[] = []
    for (const [label, data, expected] of cases) {
      route(data)
      const { rc } = await run()
      expect({ label, n: rc['units_served_unverified_tier'] }).toEqual({ label, n: expected })
      exhaustive.push(rc['exhaustive'])
    }
    // disclosure only: the verified and the unverified-tier runs have the SAME exhaustive value
    expect(exhaustive[0]).toBe(exhaustive[1])
  })

  it('detail wording: a source_incomplete leg does not claim its rows carry a tier ("each row carries ..."), a served leg points at tier_breakdown', async () => {
    route({ lagna: lagnaRows('floored'), yogi: yogiRows('floored'), tajaka: [] })
    const { unit } = await run()
    for (const u of Object.values(unit)) {
      expect(String(u['detail'])).not.toMatch(/each row carries|the row carries/)
      expect(String(u['detail'])).toMatch(/any rows served carry|a served row carries/)
    }
    route({ lagna: lagnaRows('single'), yogi: yogiRows('classical_match'), tajaka: [tajakaRow('classical_match')] })
    const served = await run()
    expect(String(served.unit.lagna['detail'])).toMatch(/tier_breakdown \/ verified_count/)
  })

  it('the special_lagnas unit never claims a tier in its own wording', async () => {
    route({ lagna: lagnaRows('single'), yogi: yogiRows('classical_match'), tajaka: [tajakaRow('classical_match')] })
    const { unit } = await run()
    expect(String(unit.lagna['detail'])).not.toContain('two_pass_verified')
  })
})
