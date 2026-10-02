/**
 * register_d9_judgment.l2_lineage_flag.test.ts — N-91 echo-class disclosure, judgment_query wiring.
 *
 * Runs the REAL judgment_query handler (wealth) with the DB, the served generation and address
 * resolution stubbed (same pattern as register_d9_judgment.wealth_leg_tiers.test.ts) and the REAL
 * lineage detector over a SQL-routed `query` mock. Pins what the handler DOES:
 *   - stale L2 pin  -> content.judgment_flags carries `l2_receipts_predate_l1`;
 *   - current pin   -> no lineage flag;
 *   - detector query error -> `l2_lineage_check_failed` (fail closed), the response still serves;
 *   - the handler's own lineage check is one SELECT (the composed query_signals call adds its own on
 *     a memo miss; each is a ~1 ms receipts read).
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
import { __clearRetrievalCache } from '../../../cache'

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

type Lineage = 'stale' | 'current' | 'error'

function route(lineage: Lineage) {
  queryMock.mockImplementation(async (sql: string) => {
    const t = String(sql)
    if (t.includes('asset_output_digest_specs') && t.includes('l1_pins')) {
      if (lineage === 'error') throw new Error('permission denied for table asset_provenance_receipts')
      const l1Digest = lineage === 'stale' ? 'NEW-L1-DIGEST' : 'PINNED-DIGEST'
      return {
        rows: [
          { asset_id: 'ga_structural', chart_id: CHART_ID, partition_key: '__whole_asset__', receipt_state: 'proven', observed_at: new Date('2026-10-04T10:00:00Z'), output_digest: l1Digest, spec_active: true, registry_current: true, l1_pins: null },
          { asset_id: 'bo_laksana', chart_id: CHART_ID, partition_key: '__whole_asset__', receipt_state: 'proven', observed_at: new Date('2026-09-08T18:22:33Z'), output_digest: 'l2', spec_active: true, registry_current: true,
            l1_pins: [{ asset_id: 'ga_structural', output_digest: 'PINNED-DIGEST', observed_at: '2026-09-07T08:37:20Z' }] },
        ],
      }
    }
    if (t.includes('brahma_vichara_constants')) {
      return { rows: [{ value_jsonb: {
        wealth: { vargas: ['D1', 'D9', 'D11'], operative: 'D9' }, career: { vargas: ['D1', 'D10'] },
        marriage: { vargas: ['D1', 'D9'] }, health: { vargas: ['D1'] }, general: { vargas: ['D1'] } } }] }
    }
    return { rows: [] }
  })
}

// query_signals (called inside judgment_query for yoga corroboration) rides a 60 s in-process memo;
// clear it so each test sees a cold path.
beforeEach(() => { queryMock.mockReset(); __clearRetrievalCache() })

async function run() {
  const r = await judgmentQueryCapability.handler({ chart_id: CHART_ID, domain: 'wealth' }, undefined)
  expect(r.is_error, JSON.stringify(r.content).slice(0, 300)).toBe(false)
  const c = r.content as Record<string, unknown>
  const flags = (c['judgment_flags'] as Array<{ code: string; detail?: string } | string>)
  const codes = flags.map(f => (typeof f === 'string' ? f : f.code))
  return { flags, codes }
}

const lineageSelects = () => queryMock.mock.calls.filter(([sql]) => String(sql).includes('asset_output_digest_specs') && String(sql).includes('l1_pins')).length

describe('judgment_query — L2 lineage flag wiring', () => {
  it('stale L2 pin: content.judgment_flags carries l2_receipts_predate_l1 naming the stale L2 asset', async () => {
    route('stale')
    const { flags, codes } = await run()
    expect(codes).toContain('l2_receipts_predate_l1')
    expect(codes).not.toContain('l2_lineage_check_failed')
    const f = flags.find(x => typeof x !== 'string' && x.code === 'l2_receipts_predate_l1') as { detail: string }
    expect(f.detail).toContain('bo_laksana')
    expect(f.detail).toContain('1 L1 asset(s)')
    expect(lineageSelects()).toBeGreaterThanOrEqual(1)
  })

  it('current pin: no lineage flag', async () => {
    route('current')
    const { codes } = await run()
    expect(codes).not.toContain('l2_receipts_predate_l1')
    expect(codes).not.toContain('l2_lineage_check_failed')
    expect(lineageSelects()).toBeGreaterThanOrEqual(1)
  })

  it('detector error: fail closed — l2_lineage_check_failed is served and the response still serves', async () => {
    route('error')
    const { codes } = await run()
    expect(codes).toContain('l2_lineage_check_failed')
    expect(codes).not.toContain('l2_receipts_predate_l1')
  })
})
